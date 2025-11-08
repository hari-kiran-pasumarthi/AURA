from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from backend.routers.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from groq import Groq
import os, json, tempfile, whisper, fitz, pytesseract, re, asyncio
from PIL import Image
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
# File storage setup (Shared with frontend)
# ---------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(PROJECT_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

# ---------------------------
# Email notifier
# ---------------------------
async def send_summary_email(user_email: str, title: str, summary: str):
    """Send an async email to the user when summarization completes."""
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
        subtype="html"
    )
    await fm.send_message(message)

# ---------------------------
# Helpers
# ---------------------------
def flatten_list(items):
    if isinstance(items, list):
        return [str(i.get("description", i)) if isinstance(i, dict) else str(i) for i in items]
    return []

def save_autonote_to_server(title, transcript, summary, highlights, bullets, user_email):
    """Save summary & metadata to JSON + text file."""
    try:
        preview = summary or (transcript[:200] + "...") if transcript else "[No content]"
        entry = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "email": user_email,
            "title": title,
            "summary": summary,
            "content": preview,
            "transcript": transcript,
            "highlights": highlights,
            "keywords": highlights,
            "bullets": bullets,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Save JSON metadata
        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Save note as .txt file
        txt_filename = f"{entry['id']}_{user_email.replace('@', '_')}.txt"
        txt_path = os.path.join(SAVE_DIR, txt_filename)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"🧠 AutoNote Entry\nUser: {user_email}\nTitle: {title}\nTimestamp: {entry['timestamp']}\n\n")
            f.write("=== Summary ===\n" + (summary or "") + "\n\n")
            f.write("=== Highlights ===\n" + "\n".join(highlights or []) + "\n\n")
            f.write("=== Bullets ===\n" + "\n".join(bullets or []) + "\n\n")
            f.write("=== Transcript ===\n" + (transcript or ""))

        # Send notification asynchronously
        asyncio.create_task(send_summary_email(user_email, title, summary))

        print(f"✅ AutoNote saved successfully for {user_email}")

    except Exception as e:
        print(f"⚠️ Failed to save AutoNote: {e}")

# ---------------------------
# Summarization (Groq)
# ---------------------------
def summarize_content(text: str, user_email: str):
    if not text or not text.strip():
        raise HTTPException(400, "Input text is empty.")

    prompt = f"""
You are an intelligent study assistant.
Summarize the following text clearly.

Output ONLY valid JSON in this format:
{{
  "summary": "<short summary>",
  "highlights": ["<3–5 key phrases>"],
  "bullets": ["<short study points>"]
}}

Text:
\"\"\"{text}\"\"\""""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        ai_output = response.choices[0].message.content.strip()

        # Extract valid JSON
        start, end = ai_output.find("{"), ai_output.rfind("}")
        if start != -1 and end != -1:
            parsed = json.loads(ai_output[start:end+1])
            summary = parsed.get("summary", "").strip()
            highlights = flatten_list(parsed.get("highlights", []))
            bullets = flatten_list(parsed.get("bullets", []))
            save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets, user_email)
            return {"summary": summary, "highlights": highlights, "bullets": bullets}

        raise ValueError("Invalid JSON output")

    except Exception as e:
        raise HTTPException(500, f"Summarization failed: {e}")

# ---------------------------
# Endpoints
# ---------------------------

@router.post("/transcribe")
async def summarize_text(req: dict, current_user: User = Depends(get_current_user)):
    """Summarize plain text."""
    text = req.get("text", "")
    result = summarize_content(text, current_user.email)
    return result


@router.post("/audio")
async def summarize_audio(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Transcribe & summarize audio."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name

    model = whisper.load_model("base")
    result = model.transcribe(temp_audio_path)
    os.remove(temp_audio_path)

    transcript = result.get("text", "")
    summary_data = summarize_content(transcript, current_user.email)
    return {"transcript": transcript, **summary_data}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Extract and summarize uploaded text or PDF file."""
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
        return summarize_content(content, current_user.email)
    except Exception as e:
        raise HTTPException(500, f"File upload failed: {e}")


@router.post("/save")
async def manual_save(note: dict, current_user: User = Depends(get_current_user)):
    """Save manual AutoNote from frontend."""
    note["id"] = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    note["timestamp"] = datetime.utcnow().isoformat()
    note["email"] = current_user.email
    note["keywords"] = note.get("highlights", [])
    with open(SAVE_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(note)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
    asyncio.create_task(send_summary_email(current_user.email, note.get("title", "Manual Note"), note.get("summary", "")))
    return {"message": "Note saved successfully!", "id": note["id"], "email": current_user.email}


@router.get("/saved")
async def get_saved_autonotes(current_user: User = Depends(get_current_user)):
    """Return all saved autonotes for the current user."""
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_notes = [n for n in data if n.get("email") == current_user.email]
    user_notes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": user_notes}
