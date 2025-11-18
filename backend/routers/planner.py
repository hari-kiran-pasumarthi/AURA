from fastapi import APIRouter, HTTPException, Depends, Body
from backend.models.schemas import PlannerRequest, PlannerResponse
from backend.services import planner
from backend.routers.auth import get_current_user
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from datetime import datetime
import os, json, asyncio

router = APIRouter(prefix="/planner", tags=["Planner"])

# =====================================================================
# 📁 Directory Setup
# =====================================================================
SAVE_DIR = os.path.join("saved_files", "planner_schedules")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "planner_log.json")
TASKS_FILE = os.path.join(SAVE_DIR, "tasks.json")

for f in [SAVE_FILE, TASKS_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump([], file, indent=2)


# =====================================================================
# 📧 Email Helper
# =====================================================================
async def send_planner_email(user_email: str, summary: str, schedule: list):
    try:
        fm = FastMail(conf)
        subject = "📅 AURA | Study Plan Confirmed!"
        body = f"""
        <h3>🧠 AURA Study Plan Scheduled</h3>
        <p><b>Summary:</b> {summary}</p>
        <p><b>Total Sessions:</b> {len(schedule)}</p>
        <hr>
        <p>Your study schedule has been added successfully.</p>
        <p style="color:gray;font-size:12px;">This is an automated message from AURA.</p>
        """
        message = MessageSchema(
            subject=subject,
            recipients=[user_email],
            body=body,
            subtype="html",
        )
        await fm.send_message(message)
    except Exception as e:
        print(f"⚠️ Email sending failed: {e}")


# =====================================================================
# 📅 Generate Plan
# =====================================================================
@router.post("/generate", response_model=PlannerResponse)
async def generate_plan(
    req: PlannerRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    try:
        print("🔑 Current user:", current_user.get("email"))

        if not req.tasks:
            raise HTTPException(400, "No tasks provided")

        # ---------------------------
        # ⭐ Convert RoutineItem objects → dicts
        # ---------------------------
        routine_slots = []
        if hasattr(req, "routine") and req.routine:
            for r in req.routine:
                routine_slots.append({
                    "label": r.label,
                    "start": r.start,
                    "end": r.end,
                })

            print(f"⏳ Custom routine converted → dict ({len(routine_slots)} slots)")
        else:
            print("ℹ️ No custom routine sent — using default routine")

        # Debug tasks
        for t in req.tasks:
            print(f"📘 Task: {t.name} | Due: {t.due} | Difficulty: {t.difficulty}")

        # Parse start_datetime
        start_dt = req.start_datetime
        if isinstance(start_dt, str):
            start_dt = datetime.fromisoformat(start_dt)
            req.start_datetime = start_dt

        print("⏰ Using start_datetime:", req.start_datetime.isoformat())

        # ---------------------------
        # ⭐ Pass routine_slots to planner
        # ---------------------------
        response = planner.generate(req, custom_routine=routine_slots)

        print(
            f"✅ Plan generated successfully for {current_user['email']} "
            f"({len(response.schedule)} days)"
        )

        # Send email asynchronously
        asyncio.create_task(send_planner_email(
            current_user["email"],
            "Your AI Study Plan is Ready!",
            response.schedule,
        ))

        return response

    except Exception as e:
        print(f"❌ Planner generation error: {e}")
        raise HTTPException(500, f"Planner generation failed: {e}")


# =====================================================================
# 💾 Save Plan (Routine Included)
# =====================================================================
@router.post("/save")
async def save_plan(data: dict, current_user: dict = Depends(get_current_user)):
    try:
        summary = data.get("summary", "Untitled Plan")
        schedule = data.get("schedule", [])
        tasks = data.get("tasks", [])
        routine = data.get("routine", [])
        date_str = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

        if not schedule:
            raise HTTPException(400, "Missing schedule data.")

        entry = {
            "email": current_user["email"],
            "summary": summary,
            "date": date_str,
            "routine": routine,
            "schedule": schedule,
            "tasks": tasks,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Append to log
        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data_log = json.load(f)
            data_log.append(entry)
            f.seek(0)
            json.dump(data_log, f, indent=2)

        # Save individual entry
        file_name = (
            f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_"
            f"{current_user['email'].replace('@','_')}.json"
        )
        file_path = os.path.join(SAVE_DIR, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)

        asyncio.create_task(
            send_planner_email(current_user["email"], summary, schedule)
        )

        print(f"💾 Saved planner entry for {current_user['email']}")
        return {"message": "Plan saved successfully", "file": file_name}

    except Exception as e:
        print(f"❌ Save failed: {e}")
        raise HTTPException(500, f"Failed to save plan: {e}")


# =====================================================================
# 📂 Fetch Saved Plans
# =====================================================================
@router.get("/saved")
async def get_saved_plans(current_user: dict = Depends(get_current_user)):
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_plans = [d for d in data if d.get("email") == current_user["email"]]
        user_plans.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {"entries": user_plans}

    except Exception as e:
        raise HTTPException(500, f"Failed to load saved plans: {e}")
