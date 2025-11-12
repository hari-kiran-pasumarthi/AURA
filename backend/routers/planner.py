from fastapi import APIRouter, HTTPException, Depends, Body
from backend.models.schemas import PlannerRequest, PlannerResponse
from backend.services import planner
from backend.services.smart_calendar import save_to_calendar, list_calendar
from backend.routers.auth import get_current_user
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
TASKS_FILE = os.path.join(SAVE_DIR, "tasks.json")

for f in [SAVE_FILE, TASKS_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([], file, indent=2)

# ---------------------------
# 📧 Email Helper
# ---------------------------
async def send_planner_email(user_email: str, summary: str, schedule: list):
    """Send a confirmation email after generating a study plan."""
    try:
        fm = FastMail(conf)
        subject = "📅 AURA | Study Plan Confirmed!"
        body = f"""
        <h3>🧠 AURA Study Plan Scheduled</h3>
        <p><b>Summary:</b> {summary}</p>
        <p><b>Total Sessions:</b> {len(schedule)}</p>
        <hr>
        <p>Your study schedule has been added successfully. 
        You'll receive reminders before each session.</p>
        <p style="color:gray;font-size:12px;">This is an automated message from AURA.</p>
        """
        message = MessageSchema(subject=subject, recipients=[user_email], body=body, subtype="html")
        await fm.send_message(message)
    except Exception as e:
        print(f"⚠️ Email sending failed: {e}")

# ---------------------------
# 📅 Generate Plan
# ---------------------------
@router.post("/generate", response_model=PlannerResponse)
async def generate_plan(req: PlannerRequest = Body(...), current_user: dict = Depends(get_current_user)):
    """Generate a personalized AI-assisted study plan."""
    try:
        print("🔑 Current user:", current_user.get("email"))

        if not req.tasks or len(req.tasks) == 0:
            raise HTTPException(status_code=400, detail="No tasks provided. Please include at least one task.")

        # 🧭 Log and validate datetime values from frontend
        for t in req.tasks:
            if not isinstance(t.due, datetime):
                raise HTTPException(status_code=400, detail=f"Invalid datetime format for task '{t.name}'")
            print(f"📘 Task: {t.name} | Due: {t.due.isoformat()} | Difficulty: {t.difficulty}")

        # Call planner logic
        response = planner.generate(req)
        print(f"✅ Plan generated successfully for {current_user['email']}")

        # Send notification email asynchronously
        asyncio.create_task(send_planner_email(current_user["email"], "Your AI Study Plan is Ready!", response.schedule))

        return response
    except Exception as e:
        print(f"❌ Planner generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Planner generation failed: {str(e)}")

# ---------------------------
# 💾 Save Plan
# ---------------------------
@router.post("/save")
async def save_plan(data: dict, current_user: dict = Depends(get_current_user)):
    """Save a generated or custom study plan."""
    try:
        summary = data.get("summary", "Untitled Plan")
        schedule = data.get("schedule", [])
        tasks = data.get("tasks", [])
        date = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

        if not schedule:
            raise HTTPException(400, "Missing schedule data.")

        entry = {
            "email": current_user["email"],
            "summary": summary,
            "date": date,
            "schedule": schedule,
            "tasks": tasks,
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data_log = json.load(f)
            data_log.append(entry)
            f.seek(0)
            json.dump(data_log, f, indent=2)

        file_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user['email'].replace('@','_')}.json"
        file_path = os.path.join(SAVE_DIR, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)

        asyncio.create_task(send_planner_email(current_user["email"], summary, schedule))
        print(f"💾 Saved planner entry for {current_user['email']}")
        return {"message": "Plan saved successfully", "file": file_name}

    except Exception as e:
        print(f"❌ Save failed: {e}")
        raise HTTPException(500, f"Failed to save plan: {e}")

# ---------------------------
# 📂 Fetch Saved Plans
# ---------------------------
@router.get("/saved")
async def get_saved_plans(current_user: dict = Depends(get_current_user)):
    """Retrieve all saved study plans for the logged-in user."""
    try:
        if not os.path.exists(SAVE_FILE):
            return {"entries": []}

        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_plans = [d for d in data if d.get("email") == current_user["email"]]
        user_plans.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {"entries": user_plans}
    except Exception as e:
        raise HTTPException(500, f"Failed to load saved plans: {e}")

# ---------------------------
# 📅 Upcoming Plans
# ---------------------------
@router.get("/upcoming")
async def get_upcoming_plans(current_user: dict = Depends(get_current_user)):
    """Fetch plans starting within the next 5 minutes."""
    try:
        if not os.path.exists(SAVE_FILE):
            return {"upcoming": []}

        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        now = datetime.utcnow()
        upcoming = []

        for plan in data:
            if plan["email"] != current_user["email"]:
                continue
            for session in plan.get("schedule", []):
                try:
                    sessions = session.get("blocks", []) if "blocks" in session else [session]
                    for s in sessions:
                        # 🔄 Handle start_time correctly
                        session_time_str = f"{plan['date']} {s.get('start_time', '00:00')}"
                        session_time = datetime.strptime(session_time_str, "%Y-%m-%d %H:%M")
                        if now <= session_time <= now + timedelta(minutes=5):
                            upcoming.append({
                                "summary": plan["summary"],
                                "start_time": s["start_time"],
                                "date": plan["date"],
                            })
                except Exception as e:
                    print("⚠️ Time parse error:", e)
                    continue

        return {"upcoming": upcoming}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch upcoming plans: {e}")

# ---------------------------
# ✅ Manage Tasks
# ---------------------------
@router.post("/tasks/add")
async def add_task(task: dict, current_user: dict = Depends(get_current_user)):
    """Add a new task to the planner (supports datetime)."""
    try:
        task["created_at"] = datetime.utcnow().isoformat()
        task["email"] = current_user["email"]
        task["status"] = "pending"

        # Ensure due is valid datetime
        if "due" in task:
            try:
                datetime.fromisoformat(task["due"])
            except Exception:
                raise HTTPException(400, f"Invalid datetime format for due: {task['due']}")

        with open(TASKS_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(task)
            f.seek(0)
            json.dump(data, f, indent=2)

        return {"status": "success", "task": task}
    except Exception as e:
        raise HTTPException(500, f"Failed to add task: {e}")

@router.post("/tasks/update")
async def update_task(task_id: str, status: str, current_user: dict = Depends(get_current_user)):
    """Update or mark a task as completed."""
    try:
        if not os.path.exists(TASKS_FILE):
            raise HTTPException(404, "No task file found.")

        with open(TASKS_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            updated = False
            for task in data:
                if task.get("id") == task_id and task.get("email") == current_user["email"]:
                    task["status"] = status
                    updated = True
                    break
            f.seek(0)
            json.dump(data, f, indent=2)

        if not updated:
            raise HTTPException(404, f"Task with id '{task_id}' not found.")
        return {"status": "updated", "task_id": task_id, "new_status": status}

    except Exception as e:
        raise HTTPException(500, f"Failed to update task: {e}")
