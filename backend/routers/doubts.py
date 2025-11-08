import os, json, time, asyncio
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models.schemas import DoubtEvent, DoubtReport
from backend.services import doubt_logger
from backend.routers.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from datetime import datetime

router = APIRouter(prefix="/doubts", tags=["Silent Study Partner"])

# -------------------------------
# 📁 Centralized Save Directory
# -------------------------------
SAVE_DIR = os.path.join("saved_files", "doubts")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_FILE = os.path.join(SAVE_DIR, "saved_doubts.json")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# -------------------------------
# 📬 Email Notification Helper
# -------------------------------
async def send_doubt_email(user_email: str, topic: str, response: str):
    """Send async email when a doubt clarification is generated."""
    fm = FastMail(conf)
    subject = f"🤔 AURA | Clarification on '{topic}'"
    body = f"""
    <h3>📘 AURA Doubt Clarification Ready</h3>
    <p><b>Topic:</b> {topic}</p>
    <p><b>Clarification:</b></p>
    <blockquote>{response[:600]}...</blockquote>
    <hr>
    <p>Check your AURA app for full details and study follow-ups.</p>
    """
    message = MessageSchema(
        subject=subject,
        recipients=[user_email],
        body=body,
        subtype="html",
    )
    await fm.send_message(message)


# -------------------------------
# 🧠 Analyze & Report Doubts
# -------------------------------
@router.post("/report", response_model=DoubtReport)
async def report_doubts(
    events: List[DoubtEvent],
    current_user: User = Depends(get_current_user)
):
    """
    Analyze confusion signals and generate AI clarification per user.
    """
    result = doubt_logger.report(events)
    result_data = result.dict() if hasattr(result, "dict") else result

    # Attach user info and save automatically
    topic = result_data.get("topic", "General Doubt")
    response = result_data.get("response", "No response generated.")
    timestamp = datetime.utcnow().isoformat()

    entry = {
        "email": current_user.email,
        "topic": topic,
        "confidence": result_data.get("confidence", "N/A"),
        "response": response,
        "timestamp": timestamp,
    }

    with open(SAVE_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2)

    # Save individual .txt file
    txt_file = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.email.replace('@','_')}.txt"
    txt_path = os.path.join(SAVE_DIR, txt_file)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"User: {current_user.email}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Topic: {topic}\n")
        f.write(f"Confidence: {entry['confidence']}\n\n")
        f.write("=== Clarification ===\n")
        f.write(response)

    # Send email asynchronously
    asyncio.create_task(send_doubt_email(current_user.email, topic, response))

    return result_data


# -------------------------------
# 💾 Manual Save (Optional)
# -------------------------------
@router.post("/save")
async def save_doubt(entry: dict, current_user: User = Depends(get_current_user)):
    """
    💾 Save AI clarification to saved_files/doubts/ as JSON and send notification.
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        entry["email"] = current_user.email
        entry["timestamp"] = timestamp

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)

        # Send notification
        asyncio.create_task(
            send_doubt_email(
                current_user.email,
                entry.get("topic", "Unknown Topic"),
                entry.get("response", "No response text"),
            )
        )

        return {"status": "success", "email": current_user.email, "message": "Saved successfully!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save doubt: {e}")


# -------------------------------
# 📚 Doubt History (Per User)
# -------------------------------
@router.get("/history")
async def list_saved_doubts(current_user: User = Depends(get_current_user)):
    """
    📚 Return all saved doubts for the logged-in user.
    """
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        user_data = [d for d in all_data if d["email"] == current_user.email]
        user_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"entries": user_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load saved doubts: {e}")
