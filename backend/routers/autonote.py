from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from backend.routers.auth import get_current_user
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from groq import Groq
import os, json, tempfile, whisper, fitz, asyncio
from datetime import datetime

router = APIRouter(prefix="/autonote", tags=["AutoNote"])

# ---------------------------
# Groq / Model configuration
# ---------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is required")

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ---------------------------
# File storage setup
# ---------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(PROJECT_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

# ---------------------------
# Email notifier (Safe Async)
# ---------------------------
async def send_summary_email(user_email: str, title: str, summary: str):
    """Sends summary email safely (won’t crash if email server is unreachable)."""
    if os.getenv("DISABLE_EMAILS", "false").lower() == "true":
        print(f"📭 Email sending disabled for {user_email}")
        return

    try:
        fm = FastMail(conf)
        subject = f"AURA | Your AutoNote '{title}' has been summarized!"
        body = f"""
        <h2>🧠 AURA AutoNote Summary Ready</h2>
        <p><b>Title:</b> {title}</p>
        <p><b>Summary:</b></p>
        <p>{summary[:500]}...</p>
        <hr>
        <p>Open your AURA app to view full highlights and notes.</p>
        <p style="color:gray;font-size:12px;">This is an automated message from AURA.</p>
        """
        message = MessageSchema(
            subject=subject,
            recipients=[user_email],
            body=body,
            subtype="html",
        )
        await fm.send_message(message)
        print(f"📨 Email sent successfully to {user_email}")
    except Exception as e:
        print(f"⚠️ Email sending failed: {e}")
        return

# ---------------------------
# Helpers
# ---------------------------
def flatten_list(items):
    if isinstance(items, list):
        return [str(i.get("description", i)) if isinstance(i, dict) else str(i) for i in items]
    return []

def save_autonote_to_server(title, transcript, summary, highlights, bullets, user_email):
    """Save summarized note to JSON and send email safely."""
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
        print(f"⚠️ Failed to save AutoNote: {e}")

# ---------------------------
# Chunked Summarization (Handles long text)
# ---------------------------
def summarize_content(text: str, user_email: str):
    if not text.strip():
        raise HTTPException(400, "Input text is empty.")

    MAX_CHARS = 6000  # split for Groq
    chunks = [text[i:i + MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]
    summaries, highlights_all, bullets_all = [], [], []

    print(f"🧠 Summarizing {len(chunks)} chunks for {user_email}...")

    for idx, chunk in enumerate(chunks, start=1):
        prompt = f"""
You are a smart academic summarizer.
Summarize clearly and concisely.

Return valid JSON:
{{
  "summary": "<summary of this part>",
  "highlights": ["<keywords>"],
  "bullets": ["<study points>"]
}}

Text (Part {idx}/{len(chunks)}):
\"\"\"{chunk}\"\"\""""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            ai_output = response.choices[0].message.content.strip()
            start, end = ai_output.find("{"), ai_output.rfind("}")
            if start != -1 and end != -1:
                parsed = json.loads(ai_output[start:end + 1])
                summaries.append(parsed.get("summary", ""))
                highlights_all.extend(flatten_list(parsed.get("highlights", [])))
                bullets_all.extend(flatten_list(parsed.get("bullets", [])))
        except Exception as e:
            print(f"⚠️ Chunk {idx} failed: {e}")

    # Merge summaries
    combined_summary = "\n".join(summaries)
    merge_prompt = f"""
Combine these partial summaries into one final academic summary.

Return JSON:
{{
  "summary": "<final summary>",
  "highlights": ["<key themes>"],
  "bullets": ["<main points>"]
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

# ---------------------------
# Endpoints
# ---------------------------
@router.post("/transcribe")
async def summarize_text(req: dict, current_user: dict = Depends(get_current_user)):
    text = req.get("text", "")
    print("🔍 Current user:", current_user)
    result = summarize_content(text, current_user["email"])
    return result


@router.post("/audio")
async def summarize_audio(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """🎙 Convert audio to text using Whisper and summarize."""
    try:
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".webm"]):
            raise HTTPException(400, "Unsupported file type. Upload MP3, WAV, M4A, or WEBM.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_audio:
            data = await file.read()
            if not data:
                raise HTTPException(400, "Empty file uploaded.")
            temp_audio.write(data)
            temp_audio_path = temp_audio.name

        # Whisper chunked transcription for long audios
        model = whisper.load_model("base")
        result = model.transcribe(temp_audio_path, verbose=False, chunk_length=30)
        os.remove(temp_audio_path)

        transcript = result.get("text", "").strip()
        if not transcript:
            raise HTTPException(400, "Audio could not be transcribed clearly.")

        summary_data = summarize_content(transcript, current_user["email"])
        return {"transcript": transcript, **summary_data}

    except Exception as e:
        raise HTTPException(500, f"Audio processing failed: {e}")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """📄 Handle text/PDF uploads for summarization."""
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
            raise HTTPException(400, "Unsupported file type. Upload .txt or .pdf only.")
        if not content.strip():
            raise HTTPException(400, "File is empty or unreadable.")
        return summarize_content(content, current_user["email"])
    except Exception as e:
        raise HTTPException(500, f"File upload failed: {e}")


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
    return {"message": "Note saved successfully!", "id": note["id"], "email": current_user["email"]}


@router.get("/saved")
async def get_saved_autonotes(current_user: dict = Depends(get_current_user)):
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_notes = [n for n in data if n.get("email") == current_user["email"]]
    user_notes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": user_notes}
