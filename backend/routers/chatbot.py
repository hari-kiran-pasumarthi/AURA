from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.gpt_connector import ask_gpt

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/")
def chatbot(request: ChatRequest):
    messages = [
        {
            "role": "system",
            "content": "You are Smart Study Assistant AI. Help students with study tips, summaries, and explanations."
        },
        {"role": "user", "content": request.question},
    ]

    answer = ask_gpt(messages)

    if not answer:
        return {"error": "Failed to get response from GPT. Check server logs for details."}

    return {"answer": answer}
