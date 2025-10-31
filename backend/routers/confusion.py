from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
from datetime import datetime
import os, time, json, re

router = APIRouter(prefix="/confusion", tags=["Concept Confusion Detector"])

# =========================
# ⚙️ GROQ CONFIG
# =========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ Missing GROQ_API_KEY environment variable.")

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# =========================
# 📁 Save Directory
# =========================
SAVE_DIR = os.path.join("saved_data", "confusion")
os.makedirs(SAVE_DIR, exist_ok=True)

# =========================
# 📘 MODELS
# =========================
class ConfusionRequest(BaseModel):
    text: str

class ConfusionResponse(BaseModel):
    explanation: str


# =========================
# 🧠 MAIN ENDPOINT
# =========================
@router.post("/analyze", response_model=ConfusionResponse)
async def analyze_confusion(req: ConfusionRequest):
    topic = req.text.strip()
    if not topic:
        raise HTTPException(400, "Please provide a valid topic or question.")

    prompt = f"""
You are a patient and clear teacher.
Explain the following concept in detail, step by step, as if teaching a beginner student.
Use simple language, examples, and analogies that make it easy to understand.
If it's a complex topic, break it into clear bullet points.

Topic: {topic}
"""
    try:
        explanation = ""
        start_time = time.time()

        # ✅ STREAM RESPONSE FROM GROQ
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in completion:
            delta = getattr(chunk.choices[0].delta, "content", "") or ""
            explanation += delta

        duration = round(time.time() - start_time, 1)
        print(f"✅ Groq responded in {duration}s ({len(explanation)} chars)")

        if not explanation.strip():
            raise HTTPException(500, "🤖 AI did not return an explanation. Try rephrasing your question.")

        # ✅ Auto-save confusion explanation
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_confusion.json"
        path = os.path.join(SAVE_DIR, filename)
        data = {
            "title": topic,
            "content": explanation.strip(),
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {"explanation": explanation.strip()}

    except Exception as e:
        raise HTTPException(500, f"Confusion analysis failed: {e}")


# =========================
# 📁 SAVED ENTRIES
# =========================
@router.get("/saved")
async def get_saved_confusion():
    """Return all saved confusion explanations."""
    try:
        files = sorted(os.listdir(SAVE_DIR), reverse=True)
        entries = []
        for f in files:
            path = os.path.join(SAVE_DIR, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    entries.append({
                        "id": os.path.basename(f).split("_")[0],
                        "title": data.get("title", "Untitled Explanation"),
                        "content": data.get("content", "[No content]"),
                        "timestamp": data.get("timestamp", datetime.utcfromtimestamp(os.path.getmtime(path)).isoformat())
                    })
            except Exception as e:
                print(f"⚠️ Skipping corrupted confusion file {f}: {e}")
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(500, f"Failed to load confusion entries: {e}")

# ✅ Alias for Saved Folder
@router.get("/notes/list/confusion")
async def get_confusion_alias():
    return await get_saved_confusion()
