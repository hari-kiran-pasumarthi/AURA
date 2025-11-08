from fastapi import APIRouter, HTTPException, Depends
from backend.routers.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
import os, json, asyncio
from datetime import datetime

router = APIRouter(prefix="/calendar", tags=["Smart Calendar"])

# --------------------------
# Setup paths
# --------------------------
CALENDAR_DIR = "saved_files/calendar"
CALENDAR_PATH = os.path.join(CALENDAR_DIR, "study_calendar.json")
os.makedirs(CALENDAR_DIR, exist_ok=True)

if not os.path.exists(CALENDAR_PATH):
    with open(CALENDAR_PATH, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# --------------------------
# Email Helper
# --------------------------
async def send_calendar_email(user_email: str, subject: str, body_text: str):
    """Send async email notification for calendar changes."""
    fm = FastMail(conf)
    message = MessageSchema(
        subject=subject,
        recipients=[user_email],
        body=f"<p>{body_text}</p><hr><p>📅 Check your Smart Calendar in AURA.</p>",
        subtype="html",
    )
    await fm.send_message(message)


# --------------------------
# Routes
# --------------------------
@router.get("/list")
async def list_calendar(current_user: User = Depends(get_current_user)):
    """📅 Fetch all study sessions for the logged-in user."""
    with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter by user
    user_data = [entry for entry in data if entry.get("email") == current_user.email]
    user_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": user_data}


@router.post("/add")
async def add_calendar_event(event: dict, current_user: User = Depends(get_current_user)):
    """➕ Add a new study session to the Smart Calendar."""
    title = event.get("title", "Untitled Study Session")
    date = event.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    time = event.get("time", "00:00")
    description = event.get("description", "No details provided")

    new_entry = {
        "email": current_user.email,
        "title": title,
        "date": date,
        "time": time,
        "description": description,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(CALENDAR_PATH, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(new_entry)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Send async email confirmation
    asyncio.create_task(
        send_calendar_email(
            current_user.email,
            "🗓 AURA | New Study Session Added",
            f"Your study session '<b>{title}</b>' was added to your calendar for {date} at {time}.",
        )
    )

    return {"message": "Event added successfully", "entry": new_entry}


@router.delete("/clear")
async def clear_calendar(current_user: User = Depends(get_current_user)):
    """🧹 Clear all study sessions for the current user."""
    with open(CALENDAR_PATH, "r+", encoding="utf-8") as f:
        data = json.load(f)
        # Keep only other users' events
        filtered = [entry for entry in data if entry.get("email") != current_user.email]
        f.seek(0)
        json.dump(filtered, f, indent=2)
        f.truncate()

    # Send async email notification
    asyncio.create_task(
        send_calendar_email(
            current_user.email,
            "🧹 AURA | Calendar Cleared",
            "All your study sessions have been cleared from your Smart Calendar.",
        )
    )

    return {"status": "cleared", "message": "Your calendar has been reset."}


@router.get("/count")
async def calendar_count(current_user: User = Depends(get_current_user)):
    """📊 Count how many study sessions exist for the logged-in user."""
    if not os.path.exists(CALENDAR_PATH):
        return {"count": 0}

    with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_count = len([entry for entry in data if entry.get("email") == current_user.email])
    return {"count": user_count}
