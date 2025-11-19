from fastapi import APIRouter, HTTPException, Depends, Body
from backend.models.schemas import PlannerRequest, PlannerResponse
from backend.services import planner
from backend.services.scheduler import schedule_task, schedule_daily_summary
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
# 📅 Generate Plan  (NO MORE ROUTINE SUPPORT)
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

        # Parse start_datetime
        start_dt = req.start_datetime
        if isinstance(start_dt, str):
            try:
                start_dt = datetime.fromisoformat(start_dt)
                req.start_datetime = start_dt
            except:
                raise HTTPException(400, "Invalid start_datetime format")

        print("⏰ Planning from:", req.start_datetime)

        # ⭐ NO ROUTINE PASSED — DEFAULT ROUTINE IS ALWAYS USED
        response = planner.generate(req)

        print(
            f"✅ Plan generated successfully for {current_user['email']} "
            f"({len(response.schedule)} days)"
        )

        # Email send async
        asyncio.create_task(send_planner_email(
            current_user["email"],
            "Your AI Study Plan is Ready!",
            response.schedule,
        ))

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Planner generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Planner generation failed: {str(e)}",
        )


# =====================================================================
# 💾 Save Plan
# =====================================================================
# =====================================================================
# 💾 Save Plan + Schedule Notifications
# =====================================================================
@router.post("/save")
async def save_plan(data: dict, current_user: dict = Depends(get_current_user)):
    try:
        summary = data.get("summary", "Untitled Plan")
        schedule = data.get("schedule", [])
        tasks = data.get("tasks", [])
        date_str = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

        if not schedule:
            raise HTTPException(400, "Missing schedule data.")

        entry = {
            "email": current_user["email"],
            "summary": summary,
            "date": date_str,
            "schedule": schedule,
            "tasks": tasks,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Save log
        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            logs = json.load(f)
            logs.append(entry)
            f.seek(0)
            json.dump(logs, f, indent=2)

        # Write backup file
        file_name = (
            f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_"
            f"{current_user['email'].replace('@','_')}.json"
        )
        with open(os.path.join(SAVE_DIR, file_name), "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)

        # ================================
        # ⭐ Schedule task reminders + daily summaries
        # ================================
        for day in schedule:
            day_date = day.get("date")
            blocks = day.get("blocks", [])

            # 1. Schedule individual task reminders
            for block in blocks:
                start = block.get("start_time")
                run_at = datetime.fromisoformat(f"{day_date}T{start}:00")

                schedule_task(
                    email=current_user["email"],
                    task_name=block.get("task", "Study Session"),
                    run_time=run_at,
                )

            # 2. Schedule daily 7AM summary
            schedule_daily_summary(
                email=current_user["email"],
                date_str=day_date,
                blocks=blocks
            )

        print(f"⏰ Scheduled reminders for {current_user['email']}")

        # Send confirmation email
        asyncio.create_task(
            send_planner_email(current_user["email"], summary, schedule)
        )

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
