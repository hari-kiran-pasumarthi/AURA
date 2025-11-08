from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import TimePredictRequest, TimePredictResponse
from backend.services import time_predictor
from backend.routers.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from datetime import datetime, timedelta
import os, json, asyncio

router = APIRouter(prefix="/timepredict", tags=["StudyTime Predictor"])

# -------------------------------
# 📁 Directory Setup
# -------------------------------
SAVE_DIR = os.path.join("saved_files", "timepredict_logs")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "timepredict_master.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# -------------------------------
# 📧 Email Notification Helper
# -------------------------------
async def send_prediction_email(user_email: str, subject: str, content: str, predicted_time: float):
    """Send prediction summary email."""
    fm = FastMail(conf)
    body = f"""
    <h3>⏳ AURA Study Time Prediction</h3>
    <p><b>Summary:</b> {content}</p>
    <p><b>Predicted Study Time:</b> {predicted_time:.2f} hours</p>
    <hr>
    <p>Stay focused! AURA will remind you 5 minutes before your predicted study session ends.</p>
    """
    message = MessageSchema(subject=subject, recipients=[user_email], body=body, subtype="html")
    await fm.send_message(message)


# -------------------------------
# ⏳ Predict Study Time (User-aware)
# -------------------------------
@router.post("/predict", response_model=TimePredictResponse)
async def predict_time(req: TimePredictRequest, current_user: User = Depends(get_current_user)):
    """⏳ Predict study time using ML model (per user)"""
    try:
        response = time_predictor.train_and_predict(req)
        prediction_hours = float(response.predicted_time or 0.0)
        timestamp = datetime.utcnow().isoformat()

        # ✅ Save structured log
        entry = {
            "email": current_user.email,
            "input": req.dict(),
            "predicted_time": prediction_hours,
            "timestamp": timestamp,
        }

        # Save to global log
        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)

        # Save individual file
        file_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.email.replace('@','_')}.json"
        with open(os.path.join(SAVE_DIR, file_name), "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)

        # ✅ Email summary
        asyncio.create_task(send_prediction_email(
            user_email=current_user.email,
            subject="⏳ AURA Study Time Prediction Complete",
            content="Your personalized study duration has been estimated.",
            predicted_time=prediction_hours
        ))

        return TimePredictResponse(predicted_time=prediction_hours)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Time prediction failed: {e}")


# -------------------------------
# 📅 Notify Before End (Frontend polling)
# -------------------------------
@router.get("/notify")
async def notify_upcoming_end(current_user: User = Depends(get_current_user)):
    """
    Returns true if user's predicted study time is about to end (within 5 minutes).
    The frontend can call this endpoint every few minutes to schedule notifications.
    """
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_entries = [d for d in data if d["email"] == current_user.email]
        if not user_entries:
            return {"notify": False}

        latest = user_entries[-1]
        start_time = datetime.fromisoformat(latest["timestamp"])
        predicted_duration = timedelta(hours=float(latest["predicted_time"]))
        end_time = start_time + predicted_duration

        now = datetime.utcnow()
        if end_time - now <= timedelta(minutes=5):
            return {"notify": True, "end_time": end_time.isoformat()}

        return {"notify": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check notification status: {e}")


# -------------------------------
# 📜 Saved Predictions (Per User)
# -------------------------------
@router.get("/saved")
async def get_saved_timepredict(current_user: User = Depends(get_current_user)):
    """✅ Return saved time predictions for the logged-in user."""
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)

        user_data = [entry for entry in all_data if entry["email"] == current_user.email]
        user_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {"entries": user_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load predictions: {e}")


# ✅ Frontend compatibility alias
@router.get("/notes/list/timepredict")
async def get_timepredict_alias(current_user: User = Depends(get_current_user)):
    return await get_saved_timepredict(current_user)
