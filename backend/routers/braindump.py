from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.backend.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
import random
import os
import asyncio
from datetime import datetime
import json

router = APIRouter(prefix="/braindump", tags=["AutoSave BrainDump"])

# ---------- Request & Response Models ----------
class BrainDumpRequest(BaseModel):
    text: str

class BrainDumpResponse(BaseModel):
    organized_text: str
    file_path: str


# ---------- Helper Functions ----------
def ensure_save_paths():
    """Create required save directories/files if not present."""
    save_dir = os.path.join("saved_files", "brain_dumps")
    os.makedirs(save_dir, exist_ok=True)

    save_file = os.path.join(save_dir, "saved_brain_dumps.json")
    if not os.path.exists(save_file):
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
    return save_dir, save_file


def save_to_file(input_text: str, response_text: str, user_email: str) -> str:
    """Save both user input and organized output to a .txt and JSON."""
    save_dir, save_file = ensure_save_paths()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"braindump_{user_email.replace('@', '_')}_{timestamp}.txt"
    file_path = os.path.join(save_dir, file_name)

    # Write text file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("🧾 Brain Dump Entry\n")
        f.write(f"User: {user_email}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("\n--- User Input ---\n")
        f.write(input_text.strip() + "\n\n")
        f.write("--- Organized Response ---\n")
        f.write(response_text.strip() + "\n")

    # Save metadata to JSON
    entry = {
        "email": user_email,
        "timestamp": timestamp,
        "input_text": input_text,
        "organized_text": response_text,
        "file_path": file_path,
    }
    with open(save_file, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2)

    return file_path


async def send_notification_email(user_email: str, organized_text: str):
    """Send async email notifying user their brain dump was processed."""
    fm = FastMail(conf)
    subject = "🧠 AURA | Your BrainDump Summary is Ready!"
    body = f"""
    <h2>🧘 AURA BrainDump Organized Response</h2>
    <p><b>Your thoughts have been processed successfully!</b></p>
    <p>Here's what we generated for you:</p>
    <blockquote>{organized_text}</blockquote>
    <hr>
    <p>Open your AURA app to view and manage all your dumps.</p>
    """
    message = MessageSchema(
        subject=subject,
        recipients=[user_email],
        body=body,
        subtype="html"
    )
    await fm.send_message(message)


# ---------- Main Route ----------
@router.post("/save", response_model=BrainDumpResponse)
async def save_brain_dump(req: BrainDumpRequest, current_user: User = Depends(get_current_user)):
    """Organize user thoughts and notify via email."""
    text = req.text.strip().lower()
    user_email = current_user.email

    if not text:
        raise HTTPException(status_code=400, detail="Empty brain dump text.")

    # Simple AI-like logic
    if any(word in text for word in ["study", "exam", "test"]):
        organized_text = (
            "📚 You seem worried about your studies. Try organizing your topics into smaller chunks "
            "and review them one by one. Short, focused sessions work better than long cramming."
        )
    elif any(word in text for word in ["project", "work", "deadline"]):
        organized_text = (
            "🗂 You’re managing multiple responsibilities. List your pending tasks, set clear priorities, "
            "and focus on one task at a time to reduce stress."
        )
    elif any(word in text for word in ["tired", "anxious", "overwhelmed"]):
        organized_text = (
            "💆 It sounds like you’re overwhelmed. Take short breaks and give yourself time to recover. "
            "Remember, productivity improves when you rest and reset."
        )
    else:
        organized_text = random.choice([
            "🧠 It looks like your thoughts are scattered. Try writing down 3 key priorities to regain focus.",
            "✨ Focus on one clear goal right now. Avoid multitasking and reward yourself after completing it.",
            "📋 Create a short to-do list — start with something easy to build momentum."
        ])

    # Save locally and record in JSON
    file_path = save_to_file(req.text, organized_text, user_email)

    # Send email notification asynchronously
    asyncio.create_task(send_notification_email(user_email, organized_text))

    return {"organized_text": organized_text, "file_path": file_path}


# ---------- Retrieve all dumps for current user ----------
@router.get("/saved")
async def get_saved_brain_dumps(current_user: User = Depends(get_current_user)):
    """Return all saved brain dumps for the logged-in user."""
    _, save_file = ensure_save_paths()
    with open(save_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_data = [d for d in data if d["email"] == current_user.email]
    user_data.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"entries": user_data}
