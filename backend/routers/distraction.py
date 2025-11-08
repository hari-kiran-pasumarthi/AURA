from fastapi import APIRouter, Depends, HTTPException
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
    <p>Keep focusing! Your digital environment is now optimized for productivity. 💪</p>
    <p><i>— The AURA System</i></p>
    """
    message = MessageSchema(
        subject=subject,
        recipients=[user_email],
        body=body,
        subtype="html"
    )
    await fm.send_message(message)
    print(f"📧 Sent distraction alert email to {user_email}.")


# ----------------------------
# 🔒 API Routes
# ----------------------------
@router.post("/block", dependencies=[Depends(get_current_user)])
async def block_distractions(current_user: User = Depends(get_current_user)):
    """Block distracting apps and websites."""
    try:
        basedir = os.path.abspath(os.path.join(os.getcwd(), "scripts"))
        kill_script = os.path.join(basedir, "kill_and_rename.ps1")
        hosts_script = os.path.join(basedir, "block_domains_hosts.ps1")

        r1 = run_ps(kill_script) if os.path.exists(kill_script) else {"rc": 1, "err": "kill script not found", "out": ""}
        r2 = run_ps(hosts_script) if os.path.exists(hosts_script) else {"rc": 1, "err": "hosts script not found", "out": ""}

        result = {"kill": r1, "hosts": r2}
        log_action(current_user.email, "block", result)
        await send_distraction_email(current_user.email, "block", json.dumps(result, indent=2))
        return {"ok": True, "message": "Distractions blocked successfully.", "details": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Distraction blocking failed: {e}")


@router.post("/rollback", dependencies=[Depends(get_current_user)])
async def rollback_distraction_block(current_user: User = Depends(get_current_user)):
    """Undo distraction blocking."""
    try:
        basedir = os.path.abspath(os.path.join(os.getcwd(), "scripts"))
        rb = os.path.join(basedir, "rollback_distraction_blocker.ps1")
        res = run_ps(rb) if os.path.exists(rb) else {"rc": 1, "err": "rollback script not found", "out": ""}
        log_action(current_user.email, "rollback", res)
        await send_distraction_email(current_user.email, "rollback", json.dumps(res, indent=2))
        return {"ok": True, "message": "Rollback completed successfully.", "details": res}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {e}")


@router.get("/logs", dependencies=[Depends(get_current_user)])
async def get_distraction_logs(current_user: User = Depends(get_current_user)):
    """Fetch user-specific distraction logs."""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        user_logs = [entry for entry in data if entry.get("email") == current_user.email]
        return {"entries": user_logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {e}")
