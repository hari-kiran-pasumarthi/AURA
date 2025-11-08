import os, json, asyncio
from fastapi import APIRouter, HTTPException, Depends
from backend.routers.auth import get_current_user
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from groq import Groq  # ✅ Groq AI SDK

router = APIRouter(prefix="/doubts", tags=["Doubts"])

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
# 🤖 Initialize Groq Client
# -------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠️ Warning: GROQ_API_KEY not found in environment.")
client = Groq(api_key=GROQ_API_KEY)

# -------------------------------
# 📧 Email Notification Helper (Safe)
# -------------------------------
async def send_doubt_email(user_email: str, topic: str, response: str):
    """Send async email if SMTP works; otherwise skip gracefully."""
    try:
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
        message = MessageSchema(subject=subject, recipients=[user_email], body=body, subtype="html")
        await fm.send_message(message)
    except Exception as e:
        print(f"⚠️ Email skipped: {e}")

# -------------------------------
# 🧠 Report a Doubt (Groq-powered)
# -------------------------------
@router.post("/report")
async def report_doubt(data: dict, current_user: dict = Depends(get_current_user)):
    """
    Logs a user's question/doubt and uses Groq AI to generate a clarification.
    """
    try:
        question = data.get("question", "").strip()
        if not question:
            raise HTTPException(400, "Question cannot be empty.")

        # 🔮 Generate Groq AI response
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ⚡ You can replace this model if desired
            messages=[
                {"role": "system", "content": "You are AURA, an intelligent academic assistant who gives clear, structured answers to student doubts."},
                {"role": "user", "content": f"Explain this concept in a simple and detailed way: {question}"}
            ],
            temperature=0.7,
            max_tokens=400
        )

        clarification = response.choices[0].message.content.strip() if response.choices else "No response generated."

        # 🧾 Save the entry
        entry = {
            "email": current_user["email"],
            "topic": question,
            "response": clarification,
            "confidence": "AI-generated",
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data_log = json.load(f)
            data_log.append(entry)
            f.seek(0)
            json.dump(data_log, f, indent=2)

        # 📁 Optional text file log
        txt_file = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user['email'].replace('@','_')}.txt"
        with open(os.path.join(SAVE_DIR, txt_file), "w", encoding="utf-8") as f:
            f.write(f"User: {current_user['email']}\n")
            f.write(f"Topic: {question}\n\n")
            f.write(f"Response:\n{clarification}")

        # 📧 Send async email
        asyncio.create_task(send_doubt_email(current_user["email"], question, clarification))

        # ✅ Return structured response
        return {
            "topic": question,
            "response": clarification,
            "confidence": "High",
            "timestamp": entry["timestamp"],
        }

    except Exception as e:
        print(f"❌ Groq doubt generation error: {e}")
        raise HTTPException(500, f"Failed to record or generate doubt: {e}")

# -------------------------------
# 💾 Manual Save
# -------------------------------
@router.post("/save")
async def save_doubt(entry: dict, current_user: dict = Depends(get_current_user)):
    """Manually save a clarified doubt."""
    try:
        entry["email"] = current_user["email"]
        entry["timestamp"] = datetime.utcnow().isoformat()

        with open(SAVE_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)

        asyncio.create_task(
            send_doubt_email(
                current_user["email"],
                entry.get("topic", "Unknown Topic"),
                entry.get("response", "No response available"),
            )
        )

        return {"status": "success", "message": "Doubt saved successfully!"}
    except Exception as e:
        raise HTTPException(500, f"Failed to save doubt: {e}")

# -------------------------------
# 📜 History
# -------------------------------
@router.get("/history")
async def get_doubt_history(current_user: dict = Depends(get_current_user)):
    """Retrieve saved doubts for the current user."""
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        user_data = [d for d in all_data if d["email"] == current_user["email"]]
        user_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"entries": user_data}
    except Exception as e:
        raise HTTPException(500, f"Failed to load saved doubts: {e}")
