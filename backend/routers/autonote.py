from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from backend.routers.auth import get_current_user
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from groq import Groq
import os, json, tempfile, whisper, fitz, asyncio, traceback
from datetime import datetime

# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------
router = APIRouter(prefix="/autonote", tags=["AutoNote"])

# ---------------------------------------------------------
# Environment + Project Paths
# ---------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY missing from environment")

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(PROJECT_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

# ---------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------
class TextRequest(BaseModel):
    text: str

class ManualSaveRequest(BaseModel):
    title: str
    summary: str
    transcript: str | None = None
    highlights: list[str] | None = None
    bullets: list[str] | None = None

# ---------------------------------------------------------
# EMAIL SENDER
# ---------------------------------------------------------
async def send_summary_email(email: str, title: str, summary: str):
    """Sends summary email if email service is enabled."""
    if os.getenv("DISABLE_EMAILS", "false").lower() == "true":
        print(f"📭 Emails disabled (skipping email to {email}).")
        return

    try:
        fm = FastMail(conf)
        message = MessageSchema(
            subject=f"AURA | Your AutoNote '{title}' Summary",
            recipients=[email],
            subtype="html",
            body=f"""
                <h2>🧠 AutoNote Summary</h2>
                <p><b>Title:</b> {title}</p>
                <p><b>Summary:</b></p>
                <p>{summary[:700]}...</p>
                <hr>
                <p style="color:gray;font-size:12px;">This is an automated email from AURA.</p>
            """,
        )
        await fm.send_message(message)
        print("📨 Email sent to:", email)
    except Exception as e:
        print("⚠️ Email failed:", e)

# ---------------------------------------------------------
# JSON helper
# ---------------------------------------------------------
def flatten_list(items):
    if isinstance(items, list):
        return [
            str(i.get("description", i)) if isinstance(i, dict) else str(i)
            for i in items
        ]
    return []

# ---------------------------------------------------------
# Save note
# ---------------------------------------------------------
def save_note(title, transcript, summary, highlights, bullets, email):
    entry = {
        "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "email": email,
        "title": title,
        "summary": summary,
        "content": summary or (transcript[:200] + "...") if transcript else summary,
        "transcript": transcript,
        "highlights": highlights,
        "keywords": highlights,
        "bullets": bullets,
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump([entry], f, indent=2, ensure_ascii=False)

    asyncio.create_task(send_summary_email(email, title, summary))
    print(f"✅ AutoNote saved for {email}")
    return entry

# ---------------------------------------------------------
# Summarization Logic
# ---------------------------------------------------------
def summarize(text: str, email: str):
    if not text.strip():
        raise HTTPException(400, "Empty text")

    MAX_LEN = 6000
    chunks = [text[i:i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    summaries: list[str] = []
    highlights: list[str] = []
    bullets: list[str] = []

    print(f"🧠 Summarizing {len(chunks)} chunks for {email}...")

    for idx, chunk in enumerate(chunks, start=1):
        prompt = f"""
You are an intelligent academic summarizer.
Summarize the text clearly and concisely.

Return valid JSON only:
{{
  "summary": "<summary>",
  "highlights": ["<keywords>"],
  "bullets": ["<main points>"]
}}

Text (Part {idx}/{len(chunks)}):
\"\"\"{chunk}\"\"\""""

        try:
            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            content = res.choices[0].message.content.strip()
            s, e = content.find("{"), content.rfind("}")
            if s == -1 or e == -1:
                raise ValueError("No JSON object found in model response")

            data = json.loads(content[s:e + 1])

            summaries.append(data.get("summary", ""))
            highlights.extend(flatten_list(data.get("highlights", [])))
            bullets.extend(flatten_list(data.get("bullets", [])))

        except Exception as e:
            print(f"⚠️ Chunk {idx} failed:", e)

    final_summary = "\n".join(summaries).strip() or text[:800]

    # Save to disk + send email
    save_note(
        "AutoNote Summary",
        text,
        final_summary,
        list(set(highlights)),
        list(set(bullets)),
        email,
    )

    return {
        "summary": final_summary,
        "highlights": list(set(highlights)),
        "bullets": list(set(bullets)),
    }

# ---------------------------------------------------------
# 📝 /text — summarize plain text
# ---------------------------------------------------------
@router.post("/text")
async def summarize_text_endpoint(
    payload: TextRequest,
    current_user: dict = Depends(get_current_user),
):
    text = payload.text.strip()
    if not text:
        raise HTTPException(400, "Text is empty")
    return summarize(text, current_user["email"])

# ---------------------------------------------------------
# 🎙 /audio — summarize audio
# ---------------------------------------------------------
@router.post("/audio")
async def audio_summary(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    try:
        filename = (file.filename or "").lower()
        if not any(filename.endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".webm"]):
            raise HTTPException(400, "Invalid audio type (use MP3/WAV/M4A/WEBM)")

        # Save raw audio temporarily
        suffix = os.path.splitext(filename)[1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp.flush()
            path = tmp.name

        print(f"🎧 Audio file saved at {path}")

        try:
            model = whisper.load_model("tiny")
        except Exception as e:
            raise HTTPException(500, f"Failed to load Whisper model: {e}")

        result = model.transcribe(path)
        transcript = (result.get("text") or "").strip()

        os.remove(path)

        if not transcript:
            raise HTTPException(400, "No speech detected in audio")

        return {
            "transcript": transcript,
            **summarize(transcript, current_user["email"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Audio error: {e}")

# ---------------------------------------------------------
# 📄 /upload — summarize PDF or TXT
# ---------------------------------------------------------
@router.post("/upload")
async def upload_summary(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    try:
        filename = (file.filename or "").lower()

        if filename.endswith(".txt"):
            text = (await file.read()).decode("utf-8", errors="ignore")

        elif filename.endswith(".pdf"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name

            text = ""
            with fitz.open(tmp_path) as pdf:
                for page in pdf:
                    text += pdf.get_page_text(page.number) if hasattr(pdf, "get_page_text") else page.get_text()
            os.remove(tmp_path)

        else:
            raise HTTPException(400, "Only PDF or TXT allowed")

        if not text.strip():
            raise HTTPException(400, "File is empty or unreadable")

        return summarize(text, current_user["email"])

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"File error: {e}")

# ---------------------------------------------------------
# 🎙 /transcribe — compatibility wrapper (old clients)
# ---------------------------------------------------------
@router.post("/transcribe")
async def transcribe_wrapper(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # Old route name, same behavior as /audio
    return await audio_summary(file, current_user)

# ---------------------------------------------------------
# 💾 /save — manual save (from frontend button)
# ---------------------------------------------------------
@router.post("/save")
async def manual_save(
    payload: ManualSaveRequest,
    current_user: dict = Depends(get_current_user),
):
    entry = save_note(
        payload.title,
        payload.transcript or "",
        payload.summary,
        payload.highlights or [],
        payload.bullets or [],
        current_user["email"],
    )
    return {"message": "Note saved successfully!", "id": entry["id"]}

# ---------------------------------------------------------
# 📁 /saved — get saved autonotes
# ---------------------------------------------------------
@router.get("/saved")
async def saved_notes(current_user: dict = Depends(get_current_user)):
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}

    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    notes = [n for n in data if n.get("email") == current_user["email"]]
    notes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": notes}
