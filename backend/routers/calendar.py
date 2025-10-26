from fastapi import APIRouter, HTTPException
import os, json

router = APIRouter(prefix="/calendar", tags=["Smart Calendar"])

CALENDAR_PATH = "saved_files/calendar/study_calendar.json"
os.makedirs(os.path.dirname(CALENDAR_PATH), exist_ok=True)

@router.get("/list")
async def list_calendar():
    """📅 Fetch all saved study sessions from Smart Study Calendar"""
    if not os.path.exists(CALENDAR_PATH):
        with open(CALENDAR_PATH, "w") as f:
            json.dump([], f)
    with open(CALENDAR_PATH, "r") as f:
        data = json.load(f)
    return {"entries": data}

@router.delete("/clear")
async def clear_calendar():
    """🧹 Clear all sessions"""
    with open(CALENDAR_PATH, "w") as f:
        json.dump([], f)
    return {"status": "cleared", "message": "All study sessions removed"}

@router.get("/count")
async def calendar_count():
    """📊 Show how many sessions exist"""
    if not os.path.exists(CALENDAR_PATH):
        return {"count": 0}
    with open(CALENDAR_PATH, "r") as f:
        data = json.load(f)
    return {"count": len(data)}
