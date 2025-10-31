from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from groq import Groq
import os, json, tempfile, whisper, fitz, pytesseract, re
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
# File storage setup
# ---------------------------
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BACKEND_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

# ---------------------------
# Helpers
# ---------------------------
def flatten_list(items):
    if isinstance(items, list):
        return [str(i.get("description", i)) if isinstance(i, dict) else str(i) for i in items]
    return []

def save_autonote_to_server(title, transcript, summary, highlights, bullets):
    """Save summary & metadata to JSON + text file."""
    try:
        preview = summary or (transcript[:200] + "...") if transcript else "[No content]"
        entry = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "title": title,
            "summary": summary,
            "content": preview,
            "transcript": transcript,
            "highlights": highlights,
            "keywords": highlights,
            "bullets": bullets,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Save metadata JSON
        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Save note as .txt file
        txt_filename = f"{entry['id']}_{title.replace(' ', '_')}.txt"
        txt_path = os.path.join(SAVE_DIR, txt_filename)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"📝 AutoNote Entry\nTitle: {title}\nTimestamp: {entry['timestamp']}\n\n")
            f.write("=== Summary ===\n" + (summary or "") + "\n\n")
            f.write("=== Highlights ===\n" + "\n".join(highlights or []) + "\n\n")
            f.write("=== Bullets ===\n" + "\n".join(bullets or []) + "\n\n")
            f.write("=== Transcript ===\n" + (transcript or ""))

        print(f"✅ AutoNote saved successfully at: {txt_path}")

    except Exception as e:
        print(f"⚠️ Failed to save AutoNote: {e}")

# ---------------------------
# Summarization (Groq)
# ---------------------------
def summarize_content(text: str):
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

        # Try to extract valid JSON
        start, end = ai_output.find("{"), ai_output.rfind("}")
        if start != -1 and end != -1:
            try:
                parsed = json.loads(ai_output[start:end+1])
                summary = parsed.get("summary", "").strip()
                highlights = flatten_list(parsed.get("highlights", []))
                bullets = flatten_list(parsed.get("bullets", []))
                save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets)
                return {"summary": summary, "highlights": highlights, "bullets": bullets}
            except json.JSONDecodeError:
                pass

        # Fallback parsing
        print("⚠️ Groq output not strict JSON — applying fallback parsing.")
        summary_match = re.search(r"(?i)(summary|overview)[:\-]?\s*(.+?)(?:\n[A-Z]|$)", ai_output, re.DOTALL)
        highlights_match = re.findall(r"[\-\*\•]\s*(.+)", ai_output)
        bullets_match = re.findall(r"\d+\.\s*(.+)", ai_output)

        summary = summary_match.group(2).strip() if summary_match else ai_output[:400]
        highlights = list(dict.fromkeys([h.strip() for h in highlights_match]))[:5]
        bullets = list(dict.fromkeys([b.strip() for b in bullets_match]))[:7]

        if not summary:
            summary = "Summary not detected, fallback applied."

        save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets)
        return {"summary": summary, "highlights": highlights, "bullets": bullets}

    except Exception as e:
        raise HTTPException(500, f"Summarization failed: {e}")

# ---------------------------
# Endpoints
# ---------------------------
@router.post("/stream")
async def stream_summary(req: dict):
    """Stream summary text in real time."""
    if not req.get("text", "").strip():
        raise HTTPException(400, "Please provide text.")
    def groq_stream():
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": req["text"]}],
                stream=True,
            )
            for chunk in completion:
                delta = getattr(chunk.choices[0].delta, "content", None) or ""
                yield delta
        except Exception as e:
            yield f"\n❌ Streaming failed: {e}"
    return StreamingResponse(groq_stream(), media_type="text/plain")

@router.post("/transcribe")
async def summarize_text(req: dict):
    """Summarize plain text."""
    text = req.get("text", "")
    result = summarize_content(text)
    return result

@router.post("/audio")
async def summarize_audio(file: UploadFile = File(...)):
    """Transcribe & summarize audio."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name
    model = whisper.load_model("base")
    result = model.transcribe(temp_audio_path)
    transcript = result.get("text", "")
    os.remove(temp_audio_path)
    summary_data = summarize_content(transcript)
    return {"transcript": transcript, **summary_data}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
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
        return summarize_content(content)
    except Exception as e:
        raise HTTPException(500, f"File upload failed: {e}")

@router.post("/save")
async def manual_save(note: dict):
    """Save manual AutoNote from frontend."""
    note["id"] = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    note["timestamp"] = datetime.utcnow().isoformat()
    note["keywords"] = note.get("highlights", [])
    with open(SAVE_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(note)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {"message": "Note saved successfully!", "id": note["id"]}

@router.get("/saved")
async def get_saved_autonotes():
    """Return all saved autonotes."""
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": data}

@router.get("/notes/get/{note_id}")
async def get_autonote_detail(note_id: str):
    """Fetch a specific autonote by ID."""
    if not os.path.exists(SAVE_FILE):
        raise HTTPException(404, "No saved notes found.")
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for note in data:
        if note.get("id") == note_id:
            return note
    raise HTTPException(404, f"No note found with ID: {note_id}")

# ✅ Alias for frontend memory vault
@router.get("/notes/list/autonote")
async def get_autonote_list_alias():
    """Provides saved autonotes for compatibility with memory vault."""
    return await get_saved_autonotes()

# ✅ List all .txt files saved
@router.get("/files")
async def list_saved_txt_files():
    """List all saved .txt files for debugging or manual verification."""
    files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".txt")]
    files.sort(reverse=True)
    return {"files": files}

# ✅ Download a specific saved .txt file
@router.get("/download/{filename}")
async def download_saved_file(filename: str):
    """Download a specific saved AutoNote text file."""
    file_path = os.path.join(SAVE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found.")
    return FileResponse(file_path, media_type="text/plain", filename=filename)
