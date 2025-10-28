from fastapi import APIRouter, HTTPException
from models.schemas import PlannerRequest, PlannerResponse
from services import planner
from services.smart_calendar import save_to_calendar, list_calendar

router = APIRouter(prefix="/planner", tags=["Planner"])


@router.post("/generate", response_model=PlannerResponse)
async def generate_plan(req: PlannerRequest):
    """
    📅 Routine-Aware Study Plan Generator
    -------------------------------------
    - Calls the planner service to create daily schedules.
    - Avoids meal/sleep times and assigns smart time slots.
    - Automatically saves schedules to Smart Study Calendar.
    """
    try:
        response = planner.generate(req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planner generation failed: {e}")


@router.post("/save")
async def save_plan(data: dict):
    """
    💾 Save Generated Planner Schedule to Smart Study Calendar
    ----------------------------------------------------------
    - Endpoint used by frontend to persist plan JSON to saved_files.
    - Writes the full schedule to saved_files/calendar/study_calendar.json.
    """
    try:
        summary = data.get("summary", "")
        schedule = data.get("schedule", [])
        tasks = data.get("tasks", [])

        if not schedule:
            raise HTTPException(status_code=400, detail="No schedule found to save.")

        # ✅ Save the plan to Smart Study Calendar
        calendar_status = save_to_calendar(schedule)

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
    """
    📅 Fetch all saved planner sessions (Smart Study Calendar)
    ----------------------------------------------------------
    Returns all study sessions saved in saved_files/calendar/study_calendar.json
    for display in Saved Page or Dashboard.
    """
    try:
        entries = list_calendar()
        return {"entries": entries}  # ✅ wrapped in key 'entries'
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendar: {e}")
