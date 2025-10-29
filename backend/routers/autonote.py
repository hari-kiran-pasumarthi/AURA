from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import os, json, requests, tempfile, whisper, fitz, pytesseract, re
from PIL import Image
from datetime import datetime

router = APIRouter()

# ✅ Ollama Config
OLLAMA_BASE = os.getenv("OLLAMA_URL", "https://ollama-railway-hr3a.onrender.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")  # <-- add model name
OLLAMA_URL = f"{OLLAMA_BASE.rstrip('/')}/api/generate"  # <-- correct endpoint

def ensure_model_loaded(model_name=OLLAMA_MODEL):
    """Ensure the given model is available on the Ollama server."""
    try:
        print(f"🧠 Ensuring model '{model_name}' is available on Ollama...")
        pull_url = f"{OLLAMA_BASE.rstrip('/')}/api/pull"
        payload = {"model": model_name}
        response = requests.post(pull_url, json=payload, timeout=600)
        if response.status_code == 200:
            print(f"✅ Model '{model_name}' is ready to use.")
        else:
            print(f"⚠️ Ollama model pull failed: {response.text}")
    except Exception as e:
        print(f"❌ Error ensuring model: {e}")

# ✅ Call this once when the router loads
ensure_model_loaded()

# ✅ File Saving Paths
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BACKEND_ROOT, "saved_files", "autonote_notes")
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_FILE = os.path.join(SAVE_DIR, "saved_autonotes.json")

if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


def flatten_list(items):
    if isinstance(items, list):
        return [str(i.get("description", i)) if isinstance(i, dict) else str(i) for i in items]
    return []


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
            f.write(f"📝 AutoNote Entry\nTitle: {title}\nTimestamp: {entry['timestamp']}\n\n")
            f.write("=== Summary ===\n" + summary + "\n\n")
            f.write("=== Highlights ===\n" + "\n".join(highlights) + "\n\n")
            f.write("=== Bullets ===\n" + "\n".join(bullets) + "\n\n")
            f.write("=== Transcript ===\n" + transcript)

        print(f"✅ AutoNote saved successfully at: {txt_path}")

    except Exception as e:
        print(f"⚠️ Failed to save AutoNote: {e}")


# 🧠 --- SUMMARIZATION CORE ---
def summarize_content(text):
    """Send content to Ollama and summarize."""
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
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)

        if response.status_code != 200:
            raise HTTPException(500, f"Ollama returned {response.status_code}: {response.text}")

        result = response.json()
        ai_output = result.get("response", "").strip()

        start, end = ai_output.find("{"), ai_output.rfind("}")
        if start != -1 and end != -1:
            try:
                parsed = json.loads(ai_output[start:end + 1])
                summary = parsed.get("summary", "").strip()
                highlights = flatten_list(parsed.get("highlights", []))
                bullets = flatten_list(parsed.get("bullets", []))
                save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets)
                return {"summary": summary, "highlights": highlights, "bullets": bullets}
            except Exception:
                pass

        print("⚠️ Ollama output not JSON — applying fallback parsing.")
        summary_match = re.search(r"(?i)(summary|overview)[:\-]?\s*(.+?)(?:\n[A-Z]|$)", ai_output, re.DOTALL)
        highlights_match = re.findall(r"[\-\*\•]\s*(.+)", ai_output)
        bullets_match = re.findall(r"\d+\.\s*(.+)", ai_output)

        summary = summary_match.group(2).strip() if summary_match else ai_output[:400]
        highlights = list(set([h.strip() for h in highlights_match]))[:5]
        bullets = list(set([b.strip() for b in bullets_match]))[:7]

        if not summary:
            summary = "Summary not detected, fallback applied."

        save_autonote_to_server("AutoNote Summary", text, summary, highlights, bullets)
        return {"summary": summary, "highlights": highlights, "bullets": bullets}

    except Exception as e:
        import traceback
        print("❌ Summarization failed:\n", traceback.format_exc())
        raise HTTPException(500, f"Summarization failed: {e}")


# 📝 TEXT SUMMARIZATION
@router.post("/transcribe")
async def summarize_text(req: dict):
    text = req.get("text", "")
    result = summarize_content(text)
    return {
        "summary": result.get("summary", ""),
        "highlights": result.get("highlights", []),
        "bullets": result.get("bullets", [])
    }


# 🎧 AUDIO SUMMARIZATION
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
        "transcript": transcript,
        "summary": summary_data.get("summary", ""),
        "highlights": summary_data.get("highlights", []),
        "bullets": summary_data.get("bullets", [])
    }
