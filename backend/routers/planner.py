from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import PlannerRequest, PlannerResponse
from backend.services import planner
from backend.services.smart_calendar import save_to_calendar, list_calendar
from backend.routers.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from datetime import datetime, timedelta
import os, json, asyncio

router = APIRouter(prefix="/planner", tags=["Planner"])

# ---------------------------
# 📁 Directory Setup
# ---------------------------
SAVE_DIR = os.path.join("saved_files", "planner_schedules")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "planner_log.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# ---------------------------
# 📧 Email Helper
# ---------------------------
async def send_planner_email(user_email: str, summary: str, schedule: list):
    fm = FastMail(conf)
    subject = "📅 AURA | Study Plan Confirmed!"
    body = f"""
    <h3>🧠 AURA Study Plan Scheduled</h3>
    <p><b>Summary:</b> {summary}</p>
    <p><b>Total Tasks:</b> {len(schedule)}</p>
    <hr>
    <p>Your study schedule has been added and you’ll receive notifications before each session!</p>
    """
    message = MessageSchema(subject=subject, recipients=[user_email], body=body, subtype="html")
    await fm.send_message(message)


# ---------------------------
# 📅 Generate Plan
# ---------------------------
@router.post("/generate", response_model=PlannerResponse)
async def generate_plan(req: PlannerRequest, current_user: User = Depends(get_current_user)):
    try:
        response = planner.generate(req)
        print(f"✅ Plan generated for {current_user.email}")
        return response
    except Exception as e:
        raise HTTPException(500, f"Planner generation failed: {e}")


# ---------------------------
# 💾 Save Plan with Date & Tasks
# ---------------------------
@router.post("/save")
async def save_plan(data: dict, current_user: User = Depends(get_current_user)):
    try:
        summary = data.get("summary", "Untitled Plan")
        schedule = data.get("schedule", [])
        tasks = data.get("tasks", [])
        date = data.get("date")  # <-- selected date from frontend

        if not schedule or not date:
            raise HTTPException(400, "Missing schedule or date.")

        timestamp = datetime.utcnow().isoformat()

        # Save to JSON
        entry = {
            "email": current_user.email,
            "summary": summary,
            "date": date,
            "schedule": schedule,
            "tasks": tasks,
            "timestamp": timestamp,
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data_log = json.load(f)
            data_log.append(entry)
            f.seek(0)
            json.dump(data_log, f, indent=2)

        # Save individual plan
        file_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.email.replace('@','_')}.json"
        with open(os.path.join(SAVE_DIR, file_name), "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)

        asyncio.create_task(send_planner_email(current_user.email, summary, schedule))

        return {"message": "Plan saved successfully", "email": current_user.email, "date": date}

    except Exception as e:
        raise HTTPException(500, f"Failed to save plan: {e}")


# ---------------------------
# 📅 Upcoming Plans (for Notifications)
# ---------------------------
@router.get("/upcoming")
async def get_upcoming_plans(current_user: User = Depends(get_current_user)):
    """Fetch plans starting within the next 5 minutes."""
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        now = datetime.utcnow()
        upcoming = []
        for plan in data:
            if plan["email"] != current_user.email:
                continue
            for session in plan["schedule"]:
                try:
                    session_time = datetime.strptime(f"{plan['date']} {session['start_time']}", "%Y-%m-%d %H:%M")
                    if now <= session_time <= now + timedelta(minutes=5):
                        upcoming.append({
                            "summary": plan["summary"],
                            "start_time": session["start_time"],
                            "date": plan["date"],
                        })
                except Exception as e:
                    print("Time parse error:", e)
                    continue
        return {"upcoming": upcoming}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch upcoming plans: {e}")


# ---------------------------
# ✅ Manage Tasks
# ---------------------------
@router.post("/tasks/add")
async def add_task(task: dict, current_user: User = Depends(get_current_user)):
    """Add a task to the planner."""
    try:
        task["created_at"] = datetime.utcnow().isoformat()
        task["email"] = current_user.email
        task["status"] = "pending"

        tasks_path = os.path.join(SAVE_DIR, "tasks.json")
        if not os.path.exists(tasks_path):
            with open(tasks_path, "w") as f:
                json.dump([], f)
        with open(tasks_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(task)
            f.seek(0)
            json.dump(data, f, indent=2)

        return {"status": "success", "task": task}
    except Exception as e:
        raise HTTPException(500, f"Failed to add task: {e}")


@router.post("/tasks/update")
async def update_task(task_id: str, status: str, current_user: User = Depends(get_current_user)):
    """Mark a task as completed or update its details."""
    try:
        tasks_path = os.path.join(SAVE_DIR, "tasks.json")
        with open(tasks_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            for task in data:
                if task.get("id") == task_id and task.get("email") == current_user.email:
                    task["status"] = status
                    break
            f.seek(0)
            json.dump(data, f, indent=2)
        return {"status": "updated", "task_id": task_id, "new_status": status}
    except Exception as e:
        raise HTTPException(500, f"Failed to update task: {e}")
