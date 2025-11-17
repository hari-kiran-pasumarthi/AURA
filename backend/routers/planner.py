from fastapi import APIRouter, HTTPException, Depends, Body
from backend.models.schemas import PlannerRequest, PlannerResponse
from backend.services import planner
from backend.routers.auth import get_current_user
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from datetime import datetime
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


# ---------------------------
# 📅 Generate Plan
# ---------------------------
@router.post("/generate", response_model=PlannerResponse)
async def generate_plan(
    req: PlannerRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    try:
        print("🔑 Current user:", current_user.get("email"))

        if not req.tasks or len(req.tasks) == 0:
            raise HTTPException(
                status_code=400,
                detail="No tasks provided. Please include at least one task.",
            )

        # Debug tasks
        for t in req.tasks:
            print(f"📘 Task: {t.name} | Due: {t.due} | Difficulty: {t.difficulty}")

        # ensure start_datetime is a valid datetime (frontend sends local IST string)
        start_dt = req.start_datetime
        if isinstance(start_dt, str):
            try:
                start_dt = datetime.fromisoformat(start_dt)
                req.start_datetime = start_dt
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_datetime format. Use ISO 8601.",
                )

        print("⏰ Using start_datetime for planning:", req.start_datetime.isoformat())

        response = planner.generate(req)
        print(
            f"✅ Plan generated successfully for {current_user['email']} "
            f"({len(response.schedule)} days)"
        )

        # async email
        asyncio.create_task(
            send_planner_email(
                current_user["email"],
                "Your AI Study Plan is Ready!",
                response.schedule,
            )
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Planner generation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Planner generation failed: {str(e)}"
        )


# ---------------------------
# 💾 Save Plan
# ---------------------------
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

        # append to log file
        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data_log = json.load(f)
            data_log.append(entry)
            f.seek(0)
            json.dump(data_log, f, indent=2)

        # save individual JSON
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


# ---------------------------
# 📂 Fetch Saved Plans
# ---------------------------
@router.get("/saved")
async def get_saved_plans(current_user: dict = Depends(get_current_user)):
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
