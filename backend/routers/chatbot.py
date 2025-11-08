from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.auth import get_current_user
from backend.models.user import User
from backend.services.gpt_connector import ask_gpt
from fastapi_mail import FastMail, MessageSchema
from backend.services.mail_config import conf
from datetime import datetime
import asyncio, os, json

router = APIRouter(prefix="/chatbot", tags=["AI ChatBot"])

# -------------------------------
# Pydantic Model
# -------------------------------
class ChatRequest(BaseModel):
    question: str


# -------------------------------
# Helper Functions
# -------------------------------
SAVE_PATH = os.path.join("saved_files", "chatbot_logs.json")
os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
if not os.path.exists(SAVE_PATH):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


def log_chat(user_email: str, question: str, answer: str):
    """Save chat logs per user for future reference."""
    entry = {
        "email": user_email,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(SAVE_PATH, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"💬 Chat saved for {user_email}")


async def send_chat_email(user_email: str, question: str, answer: str):
    """Send chat summary email asynchronously."""
    fm = FastMail(conf)
    subject = "🤖 AURA | Your Smart Study Assistant Chat Summary"
    body = f"""
    <h3>🧠 AURA Chat Summary</h3>
    <p><b>Question:</b> {question}</p>
    <p><b>Answer:</b></p>
    <blockquote>{answer}</blockquote>
    <hr>
    <p>Revisit your chat history anytime in the AURA app.</p>
    """
    message = MessageSchema(
        subject=subject,
        recipients=[user_email],
        body=body,
        subtype="html",
    )
    await fm.send_message(message)


# -------------------------------
# ChatBot Endpoint
# -------------------------------
@router.post("/")
async def chatbot(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """💬 Handle chat requests and link them to user identity."""
    user_email = current_user.email
    user_question = request.question.strip()

    if not user_question:
        raise HTTPException(status_code=400, detail="Empty question received.")

    messages = [
        {
            "role": "system",
            "content": "You are AURA: a Smart Study Assistant AI. Help students with study tips, summaries, explanations, and motivation.",
        },
        {"role": "user", "content": user_question},
    ]

    # Get AI response
    answer = ask_gpt(messages)
    if not answer:
        raise HTTPException(status_code=500, detail="Failed to get response from GPT.")

    # Log conversation
    log_chat(user_email, user_question, answer)

    # Send chat summary email asynchronously
    asyncio.create_task(send_chat_email(user_email, user_question, answer))

    return {
        "email": user_email,
        "question": user_question,
        "answer": answer,
        "timestamp": datetime.utcnow().isoformat(),
    }


# -------------------------------
# Retrieve Saved Chats
# -------------------------------
@router.get("/history")
async def get_chat_history(current_user: User = Depends(get_current_user)):
    """📜 Fetch all past chats for the logged-in user."""
    if not os.path.exists(SAVE_PATH):
        return {"entries": []}

    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_chats = [c for c in data if c.get("email") == current_user.email]
    user_chats.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"entries": user_chats}
