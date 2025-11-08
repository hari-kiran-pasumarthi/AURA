from fastapi import APIRouter, Depends
from backend.auth import get_current_user
from backend.models.user import User
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
import subprocess, os, json, asyncio
from datetime import datetime

router = APIRouter(prefix="/distraction", tags=["Distraction Sniper"])

# ----------------------------
# 📁 Log Directory
# ----------------------------
LOG_DIR = "saved_files/distraction_logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "blocker_activity.json")
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# ----------------------------
# 🧠 Helper Functions
# ----------------------------
def run_ps(script_path: str):
    """Execute a PowerShell script and return results."""
    cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{script_path}"'
    proc = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return {"rc": proc.returncode, "out": proc.stdout.strip(), "err": proc.stderr.strip()}


def log_action(user_email: str, action: str, result: dict):
    """Store a record of what happened for the user."""
    entry = {
        "email": user_email,
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "result": result,
    }
    with open(LOG_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)


async def send_distraction_email(user_email: str, action: str, details: str):
    """Send async email after blocking or rollback."""
    fm = FastMail(conf)
    subject = f"🛡️ AURA | Distraction Sniper: {action.title()} Completed"
    body = f"""
    <h3>🧠 AURA Distraction Sniper Update</h3>
    <p><b>Action:</b> {action.title()}</p>
    <p><b>Details:</b></p>
    <pre>{details}</pre>
    <hr>
    <p>Keep focusing! Your
