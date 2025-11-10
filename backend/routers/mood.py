from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from backend.routers.auth import get_current_user
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from deepface import DeepFace
from datetime import datetime
import shutil, os, json, asyncio

router = APIRouter(prefix="/mood", tags=["StudyMood Logger"])

# ----------------------------
# 📁 Directory Setup
# ----------------------------
SAVE_DIR = os.path.join("saved_files", "mood_logs")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "mood_log.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

# ----------------------------
# 🧠 Model Definition
# ----------------------------
class MoodEntry(BaseModel):
    mood: str
    emoji: str
    note: str
    timestamp: int


# ----------------------------
# 📧 Email Helper
# ----------------------------
async def send_mood_email(user_email: str, mood: str, emoji: str, note: str):
    """Send an async email with mood summary."""
    try:
        fm = FastMail(conf)
        subject = f"🧠 AURA | Mood Logged: {emoji} {mood.title()}"
        note_text = note or "No note added."
        body = f"""
        <h3>🧘 AURA Mood Tracker Update</h3>
        <p><b>Mood:</b> {emoji} {mood.title()}</p>
        <p><b>Note:</b> {note_text}</p>
        <hr>
        <p>Keep tracking your emotions to improve your study performance!</p>
        """
        message = MessageSchema(
            subject=subject,
            recipients=[user_email],
            body=body,
            subtype="html",
        )
        await fm.send_message(message)
    except Exception as e:
        print(f"⚠️ Email skipped: {e}")


# ----------------------------
# 😄 Detect Mood from Image
# ----------------------------
@router.post("/detect")
async def detect_mood(image: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Detect the user's mood from a selfie or webcam image."""
    try:
        temp_path = f"temp_{image.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        print(f"📸 Analyzing mood for {current_user['email']}...")

        result = DeepFace.analyze(img_path=temp_path, actions=["emotion"], enforce_detection=False)
        os.remove(temp_path)

        mood = result[0]["dominant_emotion"]
        confidence = result[0]["emotion"].get(mood, 0)
        print(f"✅ Mood detected: {mood} ({confidence:.2f}%)")

        return {
            "email": current_user["email"],
            "mood": mood,
            "confidence": f"{confidence:.2f}%",
        }

    except Exception as e:
        print(f"❌ Mood detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


# ----------------------------
# 💾 Log Mood (with Email)
# ----------------------------
@router.post("/log")
async def log_mood(entry: MoodEntry, current_user: dict = Depends(get_current_user)):
    """Save user mood entry + send email summary."""
    try:
        timestamp_str = datetime.fromtimestamp(entry.timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")

        log_entry = {
            "email": current_user["email"],
            "mood": entry.mood,
            "emoji": entry.emoji,
            "note": entry.note,
            "timestamp": timestamp_str,
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(log_entry)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Send async email summary
        asyncio.create_task(send_mood_email(current_user["email"], entry.mood, entry.emoji, entry.note))

        print(f"✅ Mood logged for {current_user['email']}: {entry.emoji} {entry.mood}")
        return {"message": "Mood logged successfully", "email": current_user["email"], "mood": entry.mood}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log mood: {str(e)}")


# ----------------------------
# 📜 Fetch User Mood Logs
# ----------------------------
@router.get("/logs")
async def get_mood_logs(current_user: dict = Depends(get_current_user)):
    """Fetch all saved mood logs for the logged-in user."""
    try:
        if not os.path.exists(SAVE_FILE):
            return {"entries": []}

        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            all_logs = json.load(f)

        user_logs = [log for log in all_logs if log.get("email") == current_user["email"]]
        user_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {"entries": user_logs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")
