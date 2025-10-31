from fastapi import APIRouter, HTTPException
from backend.models.schemas import PlannerRequest, PlannerResponse
from backend.services import planner
from backend.services.smart_calendar import save_to_calendar, list_calendar
from datetime import datetime
import os, json

router = APIRouter(prefix="/planner", tags=["Planner"])

SAVE_DIR = os.path.join("saved_data", "planner")
os.makedirs(SAVE_DIR, exist_ok=True)


@router.post("/generate", response_model=PlannerResponse)
async def generate_plan(req: PlannerRequest):
    """📅 Routine-Aware Study Plan Generator"""
    try:
        response = planner.generate(req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planner generation failed: {e}")


@router.post("/save")
async def save_plan(data: dict):
    """💾 Save Generated Planner Schedule"""
    try:
        summary = data.get("summary", "")
        schedule = data.get("schedule", [])
        tasks = data.get("tasks", [])

        if not schedule:
            raise HTTPException(status_code=400, detail="No schedule found to save.")

        # ✅ Save to Calendar
        calendar_status = save_to_calendar(schedule)

        # ✅ Save locally for Saved Folder
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_planner.json"
        path = os.path.join(SAVE_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "message": "Plan saved successfully!",
            "calendar_saved": calendar_status,
            "summary": summary,
            "tasks_count": len(tasks),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save plan: {e}")


@router.get("/calendar/list")
async def get_calendar_entries():
    """📅 Fetch all saved planner sessions"""
    try:
        entries = list_calendar()
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendar: {e}")


@router.get("/saved")
async def get_saved_planner():
    """✅ Return all saved planners"""
    try:
        files = sorted(os.listdir(SAVE_DIR), reverse=True)
        entries = []
        for f in files:
            path = os.path.join(SAVE_DIR, f)
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                entries.append({
                    "id": os.path.basename(f).split("_")[0],
                    "title": data.get("summary", "Study Plan"),
                    "content": f"{len(data.get('schedule', []))} day schedule saved.",
                    "timestamp": datetime.utcfromtimestamp(os.path.getmtime(path)).isoformat()
                })
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(500, f"Failed to load planner entries: {e}")

# ✅ Alias
@router.get("/notes/list/planner")
async def get_planner_alias():
    return await get_saved_planner()
