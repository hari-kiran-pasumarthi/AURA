from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
import os, time

router = APIRouter()

# =========================
# ⚙️ GROQ CONFIG
# =========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ Missing GROQ_API_KEY environment variable.")

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

# =========================
# 📘 REQUEST / RESPONSE MODELS
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
Use very simple language, examples, and analogies that make it easy to understand.
If it’s a complex topic, break it into clear bullet points.

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
            delta = chunk.choices[0].delta.content or ""
            explanation += delta

        duration = round(time.time() - start_time, 1)
        print(f"✅ Groq responded in {duration}s. Length={len(explanation)} chars")

        if not explanation.strip():
            raise HTTPException(500, "🤖 AI did not return an explanation. Try rephrasing your question.")

        return {"explanation": explanation.strip()}

    except Exception as e:
        raise HTTPException(500, f"Summarization failed: {e}")
