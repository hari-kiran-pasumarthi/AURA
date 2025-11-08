from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models.schemas import FocusEvent, FocusSuggestResponse
from backend.services import focus_detect
from backend.routers.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from datetime import datetime
import time, os, json, asyncio

router = APIRouter(prefix="/focus", tags=["FocusSense"])

# ---------------------------
# Live tracking globals
# ---------------------------
latest_result = None
last_heartbeat = 0

# ---------------------------
# File storage setup
# ---------------------------
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BACKEND_ROOT, "saved_files", "focus_sessions")
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_FILE = os.path.join(SAVE_DIR, "saved_focus.json")

if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# ---------------------------
# Helper: Save focus result
# ---------------------------
def save_focus_result(result: dict, user_email: str):
    """Save focus result linked to a specific user."""
    try:
        entry = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "email": user_email,
            "title": f"Focus Session - {datetime.utcnow().strftime('%H:%M:%S')}",
            "focused": result.get("focused"),
            "reason": result.get("reason", "N/A"),
            "pomodoro_suggest": result.get("suggest_pomodoro"),
            "attention_score": result.get("attention_score", None),
            "timestamp": datetime.utcnow().isoformat(),
            "content": (
                "🧠 Focused on task ✅"
                if result.get("focused")
                else "⚠️ Distracted or inactive ❌"
            ),
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Focus result saved for {user_email}")
        return entry

    except Exception as e:
        print(f"⚠️ Failed to save focus result: {e}")


# ---------------------------
# Email Notification Helper
# ---------------------------
async def send_focus_email(user_email: str, result: dict):
    """Send an email after focus analysis."""
    fm = FastMail(conf)
    subject = f"🎯 AURA | FocusSense Session Summary"
    focused_status = "✅ Focused" if result.get("focused") else "⚠️ Distracted"
    reason = result.get("reason", "N/A")
    attention = result.get("attention_score", "N/A")

    body = f"""
    <h3>🧠 AURA FocusSense Report</h3>
    <p><b>Status:</b> {focused_status}</p>
    <p><b>Reason:</b> {reason}</p>
    <p><b>Attention Score:</b> {attention}</p>
    <p><b>Pomodoro Suggested:</b> {"Yes" if result.get("suggest_pomodoro") else "No"}</p>
    <hr>
    <p>Keep focusing! Check your AURA dashboard for performance trends.</p>
    """
    message = MessageSchema(subject=subject, recipients=[user_email], body=body, subtype="html")
    await fm.send_message(message)


# ---------------------------
# API: Receive telemetry (agent)
# ---------------------------
@router.post("/telemetry", response_model=FocusSuggestResponse)
async def receive_telemetry(
    events: List[dict],
    current_user: User = Depends(get_current_user)
):
    """
    ✅ Receives telemetry from Focus Monitor.
    Links focus events to the logged-in user.
    """
    global latest_result, last_heartbeat

    if not events:
        raise HTTPException(status_code=400, detail="No telemetry data received")

    try:
        focus_events = [FocusEvent(**e) for e in events]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid telemetry format: {e}")

    print(f"📡 Telemetry received ({len(events)} events) from {current_user.email}")

    # Run ML-based analysis
    result = focus_detect.suggest(focus_events)
    latest_result = result.dict()
    last_heartbeat = time.time()

    # Save user-specific result
    save_focus_result(latest_result, current_user.email)

    # Send async email summary
    asyncio.create_task(send_focus_email(current_user.email, latest_result))

    return result


# ---------------------------
# API: Manual simulation (frontend)
# ---------------------------
@router.post("/suggest", response_model=FocusSuggestResponse)
async def suggest_pomodoro(
    events: List[FocusEvent],
    current_user: User = Depends(get_current_user)
):
    """✅ Simulate focus analysis manually (frontend testing)."""
    if not events:
        raise HTTPException(status_code=400, detail="No focus events provided.")

    result = focus_detect.suggest(events)
    save_focus_result(result.dict(), current_user.email)
    asyncio.create_task(send_focus_email(current_user.email, result.dict()))
    return result


# ---------------------------
# API: Latest session (user-aware)
# ---------------------------
@router.get("/latest")
async def get_latest(current_user: User = Depends(get_current_user)):
    """✅ Returns the latest focus result for this user."""
    if not os.path.exists(SAVE_FILE):
        return {"focused": None, "reason": "No focus data received yet."}

    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_data = [d for d in data if d.get("email") == current_user.email]
    if not user_data:
        return {"focused": None, "reason": "No data found for this user."}

    return user_data[-1]


# ---------------------------
# API: Agent Activity
# ---------------------------
@router.get("/status")
async def get_status():
    """✅ Returns whether the focus agent is currently active."""
    global last_heartbeat
    active = (time.time() - last_heartbeat) < 20
    return {"active": active}


# ---------------------------
# API: Saved Sessions
# ---------------------------
@router.get("/saved")
async def get_saved_focus(current_user: User = Depends(get_current_user)):
    """✅ Returns all saved focus results for the logged-in user."""
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}

    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_data = [d for d in data if d.get("email") == current_user.email]
    user_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": user_data}


# ✅ Frontend compatibility alias for Saved Folder
@router.get("/notes/list/focus")
async def get_focus_alias(current_user: User = Depends(get_current_user)):
    """✅ Alias route for Memory Vault integration."""
    return await get_saved_focus(current_user)
