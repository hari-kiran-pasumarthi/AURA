from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from groq import Groq
import os, json, tempfile, whisper, fitz, pytesseract, re, traceback
from PIL import Image
from datetime import datetime

router = APIRouter(prefix="/autonote", tags=["AutoNote"])

# ✅ Groq API setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.1-8b-instant"  # ✅ Fast & lightweight for summaries

# ✅ File saving paths
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BACKEND_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")

if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# ------------------ Helpers ------------------

def flatten_list(items):
    if isinstance(items, list):
        return [str(i.get("description", i)) if isinstance(i, dict) else str(i) for i in items]
    return []


def save_autonote_to_server(title, transcript, summary, highlights, bullets):
    """Save summarized content to text + JSON for persistence."""
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

        txt_path = os.path.join(SAVE_DIR, f"{entry['id']}_{title.replace(' ', '_')}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"📝 Title: {title}\nTimestamp: {entry['timestamp']}\n\n")
            f.write("=== Summary ===\n" + summary + "\n\n")
            f.write("=== Highlights ===\n" + "\n".join(highlights) + "\n\n")
            f.write("=== Bullets ===\n" + "\n".join(bullets) + "\n\n")
            f.write("=== Transcript ===\n" + transcript)

        print(f"✅ AutoNote saved successfully at: {txt_path}")

    except Exception as e:
        print(f"⚠️ Failed to save AutoNote: {e}")


# ------------------ Core summarizer ------------------

def summarize_content(text):
    """Summarize text using Groq Llama 3.1."""
    if not text.strip():
        raise HTTPException(400, "Input text is empty.")

    prompt = f"""
You are an intelligent note summarizer.
Summarize the text into a short summary, list 3–5 highlights, and 3–5 bullet points.

Output ONLY valid JSON:
{{
  "summary": "<summary>",
  "highlights": ["<key phrases>"],
  "bullets": ["<study points>"]
}}

Text:
\"\"\"{text}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        ai_output = response.choices[0].message.content.strip()

        # Try extracting valid JSON
        start, end = ai_output.find("{"), ai_output.rfind("}")
        if start != -1 and end != -1:
            try:
                parsed = json.loads(ai_output[start:end + 1])
                summary = parsed.get("summary", "").strip()
                highlights = flatten_list(parsed.get("highlights", []))
                bullets = flatten_list(parsed.get("bullets", []))
                save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets)
                return {"summary": summary, "highlights": highlights, "bullets": bullets}
            except json.JSONDecodeError:
                pass

        # Fallback if AI doesn’t return JSON
        print("⚠️ Groq returned non-JSON output. Falling back.")
        summary = ai_output[:400]
        highlights = re.findall(r"[\-\•]\s*(.+)", ai_output)[:5]
        bullets = re.findall(r"\d+\.\s*(.+)", ai_output)[:5]

        save_autonote_to_server("AutoNote Fallback", text, summary, highlights, bullets)
        return {"summary": summary, "highlights": highlights, "bullets": bullets}

    except Exception as e:
        print("❌ Summarization failed:\n", traceback.format_exc())
        raise HTTPException(500, f"Summarization failed: {e}")


# ------------------ Endpoints ------------------

@router.post("/stream")
async def stream_summary(req: dict):
    """Stream summarized content as it’s generated."""
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
                delta = chunk.choices[0].delta.content or ""
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
    """Summarize audio using Whisper."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name

    try:
        model = whisper.load_model("base")
        result = model.transcribe(temp_audio_path)
        transcript = result.get("text", "")
        summary_data = summarize_content(transcript)
        return {"transcript": transcript, **summary_data}
    finally:
        os.remove(temp_audio_path)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Summarize a .txt or .pdf document."""
    try:
        filename = file.filename.lower()
        content = ""

        # 🧾 Handle .txt
        if filename.endswith(".txt"):
            content = (await file.read()).decode("utf-8", errors="ignore")

        # 📘 Handle .pdf
        elif filename.endswith(".pdf"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name

            text_data = ""
            with fitz.open(tmp_path) as doc:
                for page in doc:
                    text_data += page.get_text("text") + "\n"

            # 🔍 Fallback to OCR if no text layer
            if not text_data.strip():
                try:
                    for i, page in enumerate(doc):
                        pix = page.get_pixmap()
                        img_path = f"{tmp_path}_{i}.png"
                        pix.save(img_path)
                        text_data += pytesseract.image_to_string(Image.open(img_path)) + "\n"
                        os.remove(img_path)
                except Exception as ocr_err:
                    print(f"⚠️ OCR failed: {ocr_err}")

            os.remove(tmp_path)
            content = text_data

        else:
            raise HTTPException(400, "Unsupported file type. Upload .txt or .pdf only.")

        if not content.strip():
            raise HTTPException(400, "File appears empty or unreadable.")

        result = summarize_content(content)
        return result

    except Exception as e:
        print("❌ ERROR in /autonote/upload:\n", traceback.format_exc())
        raise HTTPException(500, f"File upload failed: {e}")


@router.post("/save")
async def manual_save(note: dict):
    """Save note manually."""
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
    """Fetch single note by ID."""
    if not os.path.exists(SAVE_FILE):
        raise HTTPException(404, "No saved notes found.")
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for note in data:
        if note.get("id") == note_id:
            return note
    raise HTTPException(404, f"No note found with ID: {note_id}")
