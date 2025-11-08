from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from groq import Groq
from datetime import datetime
import os, time, json, asyncio

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
SAVE_DIR = os.path.join("saved_files", "confusion_explanations")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "confusion_logs.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# =========================
# 📘 MODELS
# =========================
class ConfusionRequest(BaseModel):
    text: str

class ConfusionResponse(BaseModel):
    explanation: str


# =========================
# 📬 Email Helper
# =========================
async def send_confusion_email(user_email: str, topic: str, explanation: str):
    """Send an async email when a confusion explanation is ready."""
    fm = FastMail(conf)
    subject = f"🧠 AURA | Your Concept Explanation for '{topic}' is Ready"
    body = f"""
    <h2>💡 AURA Confusion Resolved</h2>
    <p><b>Topic:</b> {topic}</p>
    <p><b>Explanation:</b></p>
    <blockquote>{explanation[:600]}...</blockquote>
    <hr>
    <p>Open your AURA app to view the full detailed breakdown.</p>
    <p style="color:gray;font-size:12px;">This is an automated message from AURA.</p>
    """
    message = MessageSchema(
        subject=subject,
        recipients=[user_email],
        body=body,
        subtype="html",
    )
    await fm.send_message(message)


# =========================
# 🧠 MAIN ENDPOINT
# =========================
@router.post("/analyze", response_model=ConfusionResponse)
async def analyze_confusion(req: ConfusionRequest, current_user: User = Depends(get_current_user)):
    """Analyze a confusing topic and explain it clearly, linked to the logged-in user."""
    topic = req.text.strip()
    user_email = current_user.email

    if not topic:
        raise HTTPException(400, "Please provide a valid topic or question.")

    prompt = f"""
You are AURA — a clear, patient teacher.
Explain the following concept step-by-step for a beginner.
Use examples, analogies, and bullet points where helpful.
Avoid jargon and make it relatable.

Topic: {topic}
"""
    try:
        explanation = ""
        start_time = time.time()

        # ✅ Stream response from Groq
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        for chunk in completion:
            delta = getattr(chunk.choices[0].delta, "content", "") or ""
            explanation += delta

        duration = round(time.time() - start_time, 1)
        print(f"✅ Groq responded in {duration}s ({len(explanation)} chars) for {user_email}")

        if not explanation.strip():
            raise HTTPException(500, "🤖 AI did not return an explanation. Try rephrasing your question.")

        # ✅ Save explanation to JSON log
        entry = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "email": user_email,
            "title": topic,
            "content": explanation.strip(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)

        # ✅ Save individual file for archival
        file_name = f"{entry['id']}_{user_email.replace('@','_')}.txt"
        file_path = os.path.join(SAVE_DIR, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"🧠 AURA Concept Explanation\nUser: {user_email}\nTopic: {topic}\nTimestamp: {entry['timestamp']}\n\n")
            f.write(explanation.strip())

        # ✅ Send email asynchronously
        asyncio.create_task(send_confusion_email(user_email, topic, explanation))

        return {"explanation": explanation.strip()}

    except Exception as e:
        raise HTTPException(500, f"Confusion analysis failed: {e}")


# =========================
# 📁 SAVED ENTRIES
# =========================
@router.get("/saved")
async def get_saved_confusion(current_user: User = Depends(get_current_user)):
    """Return all saved confusion explanations for the logged-in user."""
    try:
        if not os.path.exists(SAVE_FILE):
            return {"entries": []}

        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_entries = [e for e in data if e.get("email") == current_user.email]
        user_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {"entries": user_entries}

    except Exception as e:
        raise HTTPException(500, f"Failed to load confusion entries: {e}")


# ✅ Alias for Frontend Compatibility
@router.get("/notes/list/confusion")
async def get_confusion_alias(current_user: User = Depends(get_current_user)):
    """Frontend-friendly alias for saved confusions."""
    return await get_saved_confusion(current_user)
