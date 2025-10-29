from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import os, json, requests, tempfile, whisper, fitz, pytesseract, re
from PIL import Image
from datetime import datetime

router = APIRouter()

# ✅ Ollama Config
OLLAMA_BASE = os.getenv("OLLAMA_URL", "https://ollama-railway-hr3a.onrender.com")

def ensure_model_loaded(OLLAMA_MODEL ="phi3:mini"):
    """Ensure the given model is available on the Ollama server."""
    try:
        print(f"🧠 Ensuring model '{OLLAMA_MODEL}' is available on Ollama...")
        pull_url = f"{OLLAMA_BASE}/api/pull"
        payload = {"model": OLLAMA_MODEL}
        response = requests.post(pull_url, json=payload, timeout=600)
        if response.status_code == 200:
            print(f"✅ Model '{OLLAMA_MODEL}' is ready to use.")
        else:
            print(f"⚠️ Ollama model pull failed: {response.text}")
    except Exception as e:
        print(f"❌ Error ensuring model: {e}")

# ✅ File Saving Paths
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BACKEND_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")

# ✅ Ensure JSON file exists
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# 🔹 Helper: Flatten lists safely
def flatten_list(items):
    if isinstance(items, list):
        return [
            i.get("description", str(i)) if isinstance(i, dict) else str(i)
            for i in items
        ]
    return []


# 🔹 Save summarized note to server
def save_autonote_to_server(title, transcript, summary, highlights, bullets):
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
            "timestamp": datetime.utcnow().isoformat()
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)

        txt_filename = f"{entry['id']}_{title.replace(' ', '_')}.txt"
        txt_path = os.path.join(SAVE_DIR, txt_filename)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("📝 AutoNote Entry\n")
            f.write(f"Title: {title}\n")
            f.write(f"Timestamp: {entry['timestamp']}\n\n")
            f.write("=== Summary ===\n")
            f.write(summary + "\n\n")
            f.write("=== Highlights ===\n")
            f.write("\n".join(highlights) + "\n\n")
            f.write("=== Bullets ===\n")
            f.write("\n".join(bullets) + "\n\n")
            f.write("=== Transcript ===\n")
            f.write(transcript)

        print(f"✅ AutoNote saved successfully at: {txt_path}")

    except Exception as e:
        print(f"⚠️ Failed to save AutoNote: {e}")


# 🧠 --- SUMMARIZATION CORE ---
def summarize_content(text):
    """Send content to Ollama and summarize with fallback parsing."""
    if not text.strip():
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
\"\"\"{text}\"\"\"
"""
    try:
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)

        if response.status_code != 200:
            raise HTTPException(500, f"Ollama returned {response.status_code}: {response.text}")

        result = response.json()
        ai_output = result.get("response", "").strip()

        # Try JSON parsing
        start, end = ai_output.find("{"), ai_output.rfind("}")
        if start != -1 and end != -1:
            try:
                parsed = json.loads(ai_output[start:end + 1])
                summary = str(parsed.get("summary", "")).strip()
                highlights = flatten_list(parsed.get("highlights", []))
                bullets = flatten_list(parsed.get("bullets", []))
                save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets)
                return {"summary": summary, "highlights": highlights, "bullets": bullets}
            except Exception:
                pass

        # Fallback if not JSON
        print("⚠️ Ollama output not JSON — applying fallback parsing.")
        summary_match = re.search(r"(?i)(summary|overview)[:\-]?\s*(.+?)(?:\n[A-Z]|$)", ai_output, re.DOTALL)
        highlights_match = re.findall(r"[\-\*\•]\s*(.+)", ai_output)
        bullets_match = re.findall(r"\d+\.\s*(.+)", ai_output)

        summary = summary_match.group(2).strip() if summary_match else ai_output[:400]
        highlights = list(set([h.strip() for h in highlights_match]))[:5]
        bullets = list(set([b.strip() for b in bullets_match]))[:7]

        if not summary:
            summary = "Summary not detected, but extracted key information."

        save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets)
        return {"summary": summary, "highlights": highlights, "bullets": bullets}

    except Exception as e:
        import traceback
        print("❌ Summarization failed:\n", traceback.format_exc())
        raise HTTPException(500, f"Summarization failed: {e}")


# ⚡ STREAMING SUMMARIZATION (Optional)
@router.post("/stream")
async def stream_summary(req: dict):
    if not req.get("text", "").strip():
        raise HTTPException(400, "Please provide text.")

    def ollama_stream():
        prompt = f"""
Summarize clearly and concisely:
\"\"\"{req['text']}\"\"\"
"""
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": True}
        with requests.post(OLLAMA_URL, json=payload, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            yield data["response"]
                    except Exception:
                        continue
        yield "\n✅ Summary complete."

    return StreamingResponse(ollama_stream(), media_type="text/plain")


# 📝 TEXT SUMMARIZATION (SAFE)
@router.post("/transcribe")
async def summarize_text(req: dict):
    text = req.get("text", "")
    result = summarize_content(text)
    return {
        "summary": str(result.get("summary", "")),
        "highlights": [str(i) for i in result.get("highlights", [])],
        "bullets": [str(i) for i in result.get("bullets", [])]
    }


# 🎧 AUDIO SUMMARIZATION (SAFE)
@router.post("/audio")
async def summarize_audio(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name

    model = whisper.load_model("base")
    result = model.transcribe(temp_audio_path)
    transcript = result.get("text", "")
    os.remove(temp_audio_path)

    summary_data = summarize_content(transcript)
    return {
        "transcript": str(transcript),
        "summary": str(summary_data.get("summary", "")),
        "highlights": [str(h) for h in summary_data.get("highlights", [])],
        "bullets": [str(b) for b in summary_data.get("bullets", [])]
    }


# 📄 FILE UPLOAD SUMMARIZATION (SAFE)
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        filename = file.filename.lower()
        content = ""

        if filename.endswith(".txt"):
            content = (await file.read()).decode("utf-8", errors="ignore")

        elif filename.endswith(".pdf"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(await file.read())
                temp_path = temp_pdf.name

            text_data = ""
            with fitz.open(temp_path) as doc:
                for page in doc:
                    text_data += page.get_text("text") + "\n"

            if not text_data.strip():
                images = []
                with fitz.open(temp_path) as doc:
                    for i, page in enumerate(doc):
                        pix = page.get_pixmap()
                        img_path = f"{temp_path}_{i}.png"
                        pix.save(img_path)
                        images.append(img_path)
                for img in images:
                    text_data += pytesseract.image_to_string(Image.open(img)) + "\n"
                    os.remove(img)
            os.remove(temp_path)
            content = text_data

        else:
            raise HTTPException(400, "Unsupported file type. Upload .txt or .pdf only.")

        if not content.strip():
            raise HTTPException(400, "File is empty or unreadable.")

        result = summarize_content(content)
        return {
            "summary": str(result.get("summary", "")),
            "highlights": [str(i) for i in result.get("highlights", [])],
            "bullets": [str(i) for i in result.get("bullets", [])]
        }

    except Exception as e:
        import traceback
        print("❌ File upload failed:\n", traceback.format_exc())
        raise HTTPException(500, f"File upload failed: {e}")


# 💾 SAVE NOTES
@router.post("/save")
async def manual_save(note: dict):
    note["id"] = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    note["timestamp"] = datetime.utcnow().isoformat()
    note["keywords"] = note.get("highlights", [])
    with open(SAVE_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(note)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Manually saved note: {note.get('title', 'Untitled')}")
    return {"message": "Note saved successfully!", "id": note["id"]}


# 📚 GET ALL SAVED NOTES
@router.get("/saved")
async def get_saved_autonotes():
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": data}


# 🗂 ALIAS FOR COMPATIBILITY
@router.get("/notes/list/autonote")
async def get_autonote_list_alias():
    return await get_saved_autonotes()


# 🔍 FETCH SINGLE NOTE
@router.get("/notes/get/{note_id}")
async def get_autonote_detail(note_id: str):
    if not os.path.exists(SAVE_FILE):
        raise HTTPException(404, "No saved notes found.")
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for note in data:
        if note.get("id") == note_id:
            return note
    raise HTTPException(404, f"No note found with ID: {note_id}")
