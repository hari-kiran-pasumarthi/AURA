from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models.schemas import FocusEvent, FocusSuggestResponse
from backend.routers.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from datetime import datetime
import os, json, asyncio, statistics, time

# Optional: camera detection, safe import
try:
    import cv2
    import mediapipe as mp
    CAMERA_AVAILABLE = True
except Exception:
    CAMERA_AVAILABLE = False
    print("⚠️ Mediapipe or OpenCV not available — camera-based focus detection disabled.")

router = APIRouter(prefix="/focus", tags=["FocusSense"])

# ---------------------------
# Configuration
# ---------------------------
STUDY_APPS = {"vscode", "code", "word", "excel", "chrome", "notion", "pdf", "jupyter", "pycharm"}

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BACKEND_ROOT, "saved_files", "focus_sessions")
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_FILE = os.path.join(SAVE_DIR, "saved_focus.json")

if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

# ======================================================
# 🧠 Focus Detection (Keyboard + Mouse + App Activity)
# ======================================================
def analyze_focus(events: List[FocusEvent]) -> dict:
    if not events:
        raise HTTPException(400, "No activity data received.")

    last_events = events[-min(20, len(events)):]
    kpm = statistics.mean([e.keys_per_min for e in last_events])
    clicks = statistics.mean([e.mouse_clicks for e in last_events])
    switches = statistics.mean([e.window_changes for e in last_events])
    study_ratio = sum(1 for e in last_events if e.is_study_app or e.app.lower() in STUDY_APPS) / len(last_events)

    attention_score = round(((kpm / 100) * 0.4 + (clicks / 10) * 0.3 + study_ratio * 0.3) - (switches * 0.05), 2)
    attention_score = max(0.0, min(1.0, attention_score))

    focused = attention_score >= 0.6
    suggest_pomodoro = attention_score < 0.8

    reason = (
        "High typing and mouse activity on productive apps."
        if focused
        else "Low engagement or frequent app switching detected."
    )

    return {
        "focused": focused,
        "attention_score": round(attention_score * 100, 2),
        "reason": reason,
        "suggest_pomodoro": suggest_pomodoro,
    }

# ======================================================
# 👀 Optional: Camera-based Detection (Safe)
# ======================================================
def detect_camera_focus(duration=10):
    """Safe camera-based focus detection (skipped on Railway)."""
    if not CAMERA_AVAILABLE:
        print("ℹ️ Skipping camera detection (not supported in this environment).")
        return 0.0

    try:
        mp_face = mp.solutions.face_detection
        face_detection = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6)
        cap = cv2.VideoCapture(0)
        start_time = time.time()
        focus_frames, total_frames = 0, 0

        while True:
            success, frame = cap.read()
            if not success:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = face_detection.process(rgb)
            total_frames += 1
            if result.detections:
                focus_frames += 1
            if time.time() - start_time > duration:
                break

        cap.release()
        face_detection.close()
        cv2.destroyAllWindows()

        focus_ratio = focus_frames / total_frames if total_frames > 0 else 0
        return round(focus_ratio, 2)
    except Exception as e:
        print(f"⚠️ Camera detection error: {e}")
        return 0.0

# ======================================================
# 💾 Save Focus Session
# ======================================================
def save_focus_result(result: dict, user_email: str):
    entry = {
        "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "email": user_email,
        "title": f"Focus Session - {datetime.utcnow().strftime('%H:%M:%S')}",
        "focused": result.get("focused"),
        "attention_score": result.get("attention_score"),
        "reason": result.get("reason"),
        "pomodoro_suggest": result.get("suggest_pomodoro"),
        "camera_attention": result.get("camera_attention", None),
        "message": result.get("message", ""),
        "timestamp": datetime.utcnow().isoformat(),
    }
    with open(SAVE_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Focus session saved for {user_email}")

# ======================================================
# 📧 Email Notification
# ======================================================
async def send_focus_email(user_email: str, result: dict):
    try:
        fm = FastMail(conf)
        subject = "🎯 AURA FocusSense Report"
        body = f"""
        <h2>🧠 FocusSense Summary</h2>
        <p><b>Status:</b> {'✅ Focused' if result.get('focused') else '⚠️ Distracted'}</p>
        <p><b>Attention Score:</b> {result.get('attention_score')}%</p>
        <p><b>Pomodoro Suggested:</b> {'Yes' if result.get('suggest_pomodoro') else 'No'}</p>
        <p><b>Camera Attention:</b> {result.get('camera_attention', 'N/A')}</p>
        <p><b>Reason:</b> {result.get('reason')}</p>
        """
        msg = MessageSchema(subject=subject, recipients=[user_email], body=body, subtype="html")
        await fm.send_message(msg)
    except Exception as e:
        print(f"⚠️ Email send failed: {e}")

# ======================================================
# 🚀 FocusSense Endpoints
# ======================================================
@router.post("/telemetry", response_model=FocusSuggestResponse)
async def receive_telemetry(events: List[FocusEvent], current_user: User = Depends(get_current_user)):
    """Analyze focus state and suggest Pomodoro if needed."""
    print(f"📡 Telemetry received from {current_user.email}")
    result = analyze_focus(events)

    # Optional camera detection
    camera_focus = detect_camera_focus(duration=8)
    result["camera_attention"] = round(camera_focus * 100, 2)
    result["attention_score"] = round((result["attention_score"] * 0.7) + (camera_focus * 100 * 0.3), 2)

    # Add motivational messages
    if result["attention_score"] >= 85:
        result["message"] = "🔥 Excellent focus! You’re in deep work mode!"
    elif result["attention_score"] >= 65:
        result["message"] = "💪 Good focus! Keep going strong."
    elif result["attention_score"] >= 45:
        result["message"] = "👀 Getting distracted — take a 5-minute break."
    else:
        result["message"] = "⚠️ Very low focus — try the Pomodoro technique."

    save_focus_result(result, current_user.email)
    asyncio.create_task(send_focus_email(current_user.email, result))
    return result

@router.get("/pomodoro")
async def get_pomodoro_plan(current_user: User = Depends(get_current_user)):
    """Provide scientifically proven Pomodoro plan."""
    return {
        "email": current_user.email,
        "pomodoro_plan": {
            "work_session": "25 minutes",
            "short_break": "5 minutes",
            "long_break": "15–30 minutes",
            "cycles_before_long_break": 4,
            "description": "Work for 25 minutes, rest for 5, repeat 4 times, then take a longer break."
        }
    }

@router.get("/saved")
async def get_saved_focus(current_user: User = Depends(get_current_user)):
    """Return saved focus sessions."""
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_data = [d for d in data if d.get("email") == current_user.email]
    user_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": user_data}
