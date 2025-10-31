from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.schemas import FocusEvent, FocusSuggestResponse
from backend.services import focus_detect
from datetime import datetime
import time, os, json

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
def save_focus_result(result: dict):
    """Save the latest focus ML result to persistent storage."""
    try:
        entry = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
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

        print(f"✅ Focus result saved at: {SAVE_FILE}")
        return entry

    except Exception as e:
        print(f"⚠️ Failed to save focus result: {e}")


# ---------------------------
# API: Receive telemetry (agent)
# ---------------------------
@router.post("/telemetry", response_model=FocusSuggestResponse)
async def receive_telemetry(events: List[dict]):
    """
    ✅ Receives telemetry from the Focus Monitor agent.
    Converts JSON → FocusEvent → ML analysis → updates live tracking.
    """
    global latest_result, last_heartbeat

    if not events:
        raise HTTPException(status_code=400, detail="No telemetry data received")

    try:
        focus_events = [FocusEvent(**e) for e in events]
    except Exception as e:
        print(f"❌ Invalid telemetry format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid telemetry format: {e}")

    print(f"📡 Telemetry received ({len(events)} events) at {time.strftime('%H:%M:%S')}")

    # Run analysis
    result = focus_detect.suggest(focus_events)
    latest_result = result.dict()
    last_heartbeat = time.time()

    # Persist to JSON
    save_focus_result(latest_result)

    print(f"✅ Focus Updated → Focused={result.focused}, Pomodoro={result.suggest_pomodoro}")
    return result


# ---------------------------
# API: Manual frontend simulation
# ---------------------------
@router.post("/suggest", response_model=FocusSuggestResponse)
async def suggest_pomodoro(events: List[FocusEvent]):
    """✅ Used by frontend for manual or simulated focus data."""
    if not events:
        raise HTTPException(status_code=400, detail="No focus events provided.")
    result = focus_detect.suggest(events)
    save_focus_result(result.dict())
    return result


# ---------------------------
# API: Latest + Agent Status
# ---------------------------
@router.get("/latest")
async def get_latest():
    """✅ Returns the most recent focus analysis result."""
    if latest_result:
        return latest_result

    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data:
            return data[-1]

    return {"focused": None, "reason": "No focus data received yet."}


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
async def get_saved_focus():
    """✅ Returns all saved focus results for Saved Folder."""
    if not os.path.exists(SAVE_FILE):
        return {"entries": []}
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": data}


# ✅ Frontend compatibility alias for Saved Folder
@router.get("/notes/list/focus")
async def get_focus_alias():
    """✅ Alias route for Memory Vault integration."""
    return await get_saved_focus()
