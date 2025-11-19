from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from backend.routers.auth import get_current_user
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from groq import Groq
import os, json, tempfile, whisper, fitz, asyncio, traceback
from datetime import datetime

router = APIRouter(prefix="/autonote", tags=["AutoNote"])

# ENV
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY missing")

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(PROJECT_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w") as f:
        json.dump([], f, indent=2)

# Models
class TextRequest(BaseModel):
    text: str

class ManualSaveRequest(BaseModel):
    title: str
    summary: str
    transcript: str | None = None
    highlights: list[str] | None = None
    bullets: list[str] | None = None

# EMAIL
async def send_summary_email(email: str, title: str, summary: str):
    if os.getenv("DISABLE_EMAILS", "false") == "true":
        return

    try:
        fm = FastMail(conf)
        message = MessageSchema(
            subject=f"AURA | AutoNote Summary: {title}",
            recipients=[email],
            body=f"""
                <h2>🧠 AutoNote Summary</h2>
                <p><b>Title:</b> {title}</p>
                <p>{summary[:700]}...</p>
            """,
            subtype="html",
        )
        await fm.send_message(message)
    except Exception as e:
        print("⚠️ Email error:", e)

# Helpers
def flatten_list(items):
    if isinstance(items, list):
        return [str(x.get("description", x)) if isinstance(x, dict) else str(x) for x in items]
    return []

def save_note(title, transcript, summary, highlights, bullets, email):
    entry = {
        "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "email": email,
        "title": title,
        "summary": summary,
        "content": summary,
        "transcript": transcript,
        "highlights": highlights,
        "keywords": highlights,
        "bullets": bullets,
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        with open(SAVE_FILE, "r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
    except:
        with open(SAVE_FILE, "w") as f:
            json.dump([entry], f, indent=2)

    asyncio.create_task(send_summary_email(email, title, summary))
    return entry

# Summarization
def summarize(text: str, email: str):
    if not text.strip():
        raise HTTPException(400, "Empty text")

    chunks = [text[i:i+6000] for i in range(0, len(text), 6000)]
    summaries, highlights, bullets = [], [], []

    for chunk in chunks:
        prompt = f"""
Summarize academically into JSON:
{{
  "summary":"",
  "highlights":[],
  "bullets":[]
}}

Text:
\"\"\"{chunk}\"\"\"
"""
        try:
            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            content = res.choices[0].message.content
            s, e = content.find("{"), content.rfind("}")
            data = json.loads(content[s:e+1])
            summaries.append(data["summary"])
            highlights.extend(flatten_list(data["highlights"]))
            bullets.extend(flatten_list(data["bullets"]))
        except:
            continue

    final_summary = "\n".join(summaries).strip() or text[:800]

    save_note("AutoNote Summary", text, final_summary, list(set(highlights)), list(set(bullets)), email)

    return {
        "summary": final_summary,
        "highlights": list(set(highlights)),
        "bullets": list(set(bullets)),
    }

# ROUTES

@router.post("/text")
async def summarize_text(payload: TextRequest, current_user: dict = Depends(get_current_user)):
    return summarize(payload.text, current_user["email"])


@router.post("/audio")
async def summarize_audio(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".webm"]):
        raise HTTPException(400, "Invalid audio type")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    model = whisper.load_model("tiny")
    result = model.transcribe(tmp_path)
    transcript = result["text"].strip()
    os.remove(tmp_path)

    if not transcript:
        raise HTTPException(400, "No speech detected")

    return {"transcript": transcript, **summarize(transcript, current_user["email"])}


@router.post("/upload")
async def summarize_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    filename = file.filename.lower()

    if filename.endswith(".txt"):
        text = (await file.read()).decode("utf-8")

    elif filename.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        text = ""
        with fitz.open(tmp_path) as pdf:
            for page in pdf:
                text += page.get_text()
        os.remove(tmp_path)
    else:
        raise HTTPException(400, "Only .pdf or .txt allowed")

    return summarize(text, current_user["email"])


@router.post("/save")
async def manual_save(payload: ManualSaveRequest, current_user: dict = Depends(get_current_user)):
    entry = save_note(
        payload.title,
        payload.transcript or "",
        payload.summary,
        payload.highlights or [],
        payload.bullets or [],
        current_user["email"]
    )
    return {"message": "Saved!", "id": entry["id"]}


@router.get("/saved")
async def saved_notes(current_user: dict = Depends(get_current_user)):
    with open(SAVE_FILE, "r") as f:
        data = json.load(f)

    notes = [n for n in data if n["email"] == current_user["email"]]
    notes.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"entries": notes}
