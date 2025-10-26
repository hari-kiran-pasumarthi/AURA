from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
import os
from datetime import datetime

router = APIRouter()

# ---------- Request & Response Models ----------
class BrainDumpRequest(BaseModel):
    text: str

class BrainDumpResponse(BaseModel):
    organized_text: str
    file_path: str  # added to show where it was saved


# ---------- Helper Function to Save Files ----------
def save_to_file(input_text: str, response_text: str) -> str:
    # Define directory path
    save_dir = os.path.join("saved_files", "brain_dumps")
    os.makedirs(save_dir, exist_ok=True)

    # Create timestamp-based filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"brain_dump_{timestamp}.txt"
    file_path = os.path.join(save_dir, file_name)

    # Write both input and output to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("🧾 Brain Dump Entry\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("\n--- User Input ---\n")
        f.write(input_text.strip() + "\n\n")
        f.write("--- Organized Response ---\n")
        f.write(response_text.strip() + "\n")

    return file_path


# ---------- Main Route ----------
@router.post("/save", response_model=BrainDumpResponse)
async def save_brain_dump(req: BrainDumpRequest):
    text = req.text.strip().lower()

    if not text:
        raise HTTPException(status_code=400, detail="Empty brain dump text.")

    # Simple AI-like logic (replace later with LLM/ML)
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
            "💆‍♀️ It sounds like you’re overwhelmed. Take short breaks and give yourself time to recover. "
            "Remember, productivity improves when you rest and reset."
        )
    else:
        generic_responses = [
            "🧠 It looks like your thoughts are scattered. Try writing down 3 key priorities to regain focus.",
            "✨ Focus on one clear goal right now. Avoid multitasking and reward yourself after completing it.",
            "📋 Create a short to-do list — start with something easy to build momentum."
        ]
        organized_text = random.choice(generic_responses)

    # Save to file
    file_path = save_to_file(req.text, organized_text)

    return {"organized_text": organized_text, "file_path": file_path}
