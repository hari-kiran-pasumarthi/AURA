from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.schemas import FocusEvent, FocusSuggestResponse
from backend.services import focus_detect
import time

router = APIRouter()

# 🧠 Global variables for live tracking
latest_result = None
last_heartbeat = 0


@router.post("/telemetry", response_model=FocusSuggestResponse)
async def receive_telemetry(events: List[dict]):
    """
    ✅ Receives telemetry from the Focus Monitor agent (Python script).
    Converts raw JSON events into FocusEvent models, analyzes them,
    and updates live status for the frontend.
    """
    global latest_result, last_heartbeat

    if not events:
        raise HTTPException(status_code=400, detail="No telemetry data received")

    # Convert dicts → FocusEvent Pydantic objects
    try:
        focus_events = [FocusEvent(**e) for e in events]
    except Exception as e:
        print(f"❌ Invalid telemetry format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid telemetry format: {e}")

    # Log for debugging
    print(f"📡 Telemetry received ({len(events)} events) at {time.strftime('%H:%M:%S')}")

    # Analyze using your ML logic
    result = focus_detect.suggest(focus_events)

    # Save latest focus result and heartbeat timestamp
    latest_result = result.dict()
    last_heartbeat = time.time()

    print(
        f"✅ Focus Analysis Updated → Focused={result.focused}, "
        f"PomodoroSuggest={result.suggest_pomodoro}"
    )

    return result


@router.post("/suggest", response_model=FocusSuggestResponse)
async def suggest_pomodoro(events: List[FocusEvent]):
    """
    ✅ Manual endpoint used by frontend for simulated focus data.
    Useful when testing without the desktop agent.
    """
    if events is None or not events:
        raise HTTPException(status_code=400, detail="No focus events provided.")
    return focus_detect.suggest(events)


@router.get("/latest")
async def get_latest():
    """
    ✅ Returns the most recent focus analysis.
    Polled every 10s by the frontend for live updates.
    """
    if latest_result:
        return latest_result
    return {"focused": None, "reason": "No focus data received yet."}


@router.get("/status")
async def get_status():
    """
    ✅ Returns whether the focus agent is active.
    Active if telemetry received within the last 20 seconds.
    """
    global last_heartbeat
    active = (time.time() - last_heartbeat) < 20
    return {"active": active}
