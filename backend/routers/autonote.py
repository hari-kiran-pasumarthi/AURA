from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from backend.routers.auth import get_current_user
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from groq import Groq
import os, json, tempfile, whisper, fitz, asyncio, traceback
from datetime import datetime

router = APIRouter(prefix="/autonote", tags=["AutoNote"])

# =====================================================
# 🔧 Configuration
# =====================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is required")

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(PROJECT_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

# =====================================================
# 📧 Email Notification
# =====================================================
async def send_summary_email(user_email: str, title: str, summary: str):
    """Send summary via email safely."""
    if os.getenv("DISABLE_EMAILS", "false").lower() == "true":
        print(f"📭 Email sending disabled for {user_email}")
        return

    try:
        fm = FastMail(conf)
        subject = f"AURA | Your AutoNote '{title}' Summary"
        body = f"""
        <h2>🧠 AURA AutoNote Summary Ready</h2>
        <p><b>Title:</b> {title}</p>
        <p><b>Summary:</b></p>
        <p>{summary[:700]}...</p>
        <hr>
        <p style="color:gray;font-size:12px;">This is an automated message from AURA.</p>
        """
        msg = MessageSchema(subject=subject, recipients=[user_email], body=body, subtype="html")
        await fm.send_message(msg)
        print(f"📨 Email sent to {user_email}")
    except Exception as e:
        print(f"⚠️ Email failed: {e}")

# =====================================================
# 🧩 Helper Functions
# =====================================================
def flatten_list(items):
    if isinstance(items, list):
        return [str(i.get("description", i)) if isinstance(i, dict) else str(i) for i in items]
    return []

def save_autonote_to_server(title, transcript, summary, highlights, bullets, user_email):
    """Save summarized note to JSON and trigger email."""
    try:
        entry = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "email": user_email,
            "title": title,
            "summary": summary,
            "content": summary or (transcript[:200] + "..."),
            "transcript": transcript,
            "highlights": highlights,
            "keywords": highlights,
            "bullets": bullets,
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)

        asyncio.create_task(send_summary_email(user_email, title, summary))
        print(f"✅ AutoNote saved for {user_email}")
    except Exception as e:
        print(f"⚠️ Save failed: {e}")

# =====================================================
# 🧠 Summarization Logic
# =====================================================
def summarize_content(text: str, user_email: str):
    if not text.strip():
        raise HTTPException(400, "Input text is empty.")

    MAX_CHARS = 6000
    chunks = [text[i:i + MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]
    summaries, highlights_all, bullets_all = [], [], []

    print(f"🧠 Summarizing {len(chunks)} chunks for {user_email}...")

    for idx, chunk in enumerate(chunks, start=1):
        prompt = f"""
You are an intelligent academic summarizer.
Summarize the text clearly and concisely.

Return valid JSON:
{{
  "summary": "<summary>",
  "highlights": ["<keywords>"],
  "bullets": ["<main points>"]
}}

Text (Part {idx}/{len(chunks)}):
\"\"\"{chunk}\"\"\""""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            content = response.choices[0].message.content.strip()
            start, end = content.find("{"), content.rfind("}")
            if start != -1 and end != -1:
                parsed = json.loads(content[start:end + 1])
                summaries.append(parsed.get("summary", ""))
                highlights_all.extend(flatten_list(parsed.get("highlights", [])))
                bullets_all.extend(flatten_list(parsed.get("bullets", [])))
        except Exception as e:
            print(f"⚠️ Chunk {idx} failed: {e}")

    # Combine all parts
    combined_summary = "\n".join(summaries)
    merge_prompt = f"""
Combine the following summaries into one refined academic summary.

Return JSON:
{{
  "summary": "<final summary>",
  "highlights": ["<key themes>"],
  "bullets": ["<study points>"]
}}

Summaries:
{combined_summary}
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": merge_prompt}],
            temperature=0.0,
        )
        merged_output = response.choices[0].message.content.strip()
        start, end = merged_output.find("{"), merged_output.rfind("}")
        if start != -1 and end != -1:
            parsed = json.loads(merged_output[start:end + 1])
            summary = parsed.get("summary", combined_summary)
            highlights = list(set(highlights_all + flatten_list(parsed.get("highlights", []))))
            bullets = list(set(bullets_all + flatten_list(parsed.get("bullets", []))))
        else:
            summary, highlights, bullets = combined_summary, highlights_all, bullets_all
    except Exception as e:
        print(f"⚠️ Merge failed: {e}")
        summary, highlights, bullets = combined_summary, highlights_all, bullets_all

    save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets, user_email)
    return {"summary": summary, "highlights": highlights, "bullets": bullets}

# =====================================================
# 🎙 Audio Transcription Endpoint
# =====================================================
@router.post("/audio")
async def summarize_audio(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """🎧 Convert uploaded audio to text and summarize."""
    try:
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".webm"]):
            raise HTTPException(400, "Unsupported file type. Upload MP3, WAV, M4A, or WEBM.")

        # Save file to temp path
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_audio:
            data = await file.read()
            if not data:
                raise HTTPException(400, "Empty audio file.")
            temp_audio.write(data)
            temp_audio.flush()
            temp_audio_path = temp_audio.name

        print(f"🎧 Audio file saved at {temp_audio_path}")

        # Load Whisper model safely
        try:
            model = whisper.load_model("tiny")
        except Exception as e:
            raise HTTPException(500, f"Failed to load Whisper: {e}")

        # Transcribe audio
        print("🎤 Starting transcription...")
        result = model.transcribe(temp_audio_path, verbose=False)
        transcript = result.get("text", "").strip()
        os.remove(temp_audio_path)

        if not transcript:
            raise HTTPException(400, "Transcription failed or empty result.")

        print(f"📝 Transcript length: {len(transcript)} chars")
        summary_data = summarize_content(transcript, current_user["email"])
        return {"transcript": transcript, **summary_data}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Audio processing failed: {e}")

# =====================================================
# 📄 File Upload Endpoint
# =====================================================
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """📘 Handle text/PDF upload for summarization."""
    try:
        filename = file.filename.lower()
        if filename.endswith(".txt"):
            content = (await file.read()).decode("utf-8", errors="ignore")
        elif filename.endswith(".pdf"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(await file.read())
                temp_pdf_path = temp_pdf.name

            content = ""
            with fitz.open(temp_pdf_path) as doc:
                for page in doc:
                    content += page.get_text("text") + "\n"
            os.remove(temp_pdf_path)
        else:
            raise HTTPException(400, "Unsupported file type. Use .txt or .pdf only.")

        if not content.strip():
            raise HTTPException(400, "File is empty or unreadable.")
        return summarize_content(content, current_user["email"])

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"File processing failed: {e}")

# =====================================================
# 🎙 Compatibility Transcription Endpoint (/transcribe)
# =====================================================
@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Compatibility wrapper so that /autonote/transcribe also works."""
    return await summarize_audio(file, current_user)


# =====================================================
# 💾 Manual Save + Retrieval
# =====================================================
@router.post("/save")
async def manual_save(note: dict, current_user: dict = Depends(get_current_user)):
    note["id"] = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    note["timestamp"] = datetime.utcnow().isoformat()
    note["email"] = current_user["email"]
    note["keywords"] = note.get("highlights", [])
    with open(SAVE_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(note)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
    asyncio.create_task(send_summary_email(current_user["email"], note.get("title", "Manual Note"), note.get("summary", "")))
    return {"message": "Note saved successfully!", "id": note["id"]}

@router.get("/saved")
async def get_saved_autonotes(current_user: dict = Depends(get_current_user)):
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_notes = [n for n in data if n.get("email") == current_user["email"]]
    user_notes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": user_notes}
