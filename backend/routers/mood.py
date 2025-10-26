from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from deepface import DeepFace
import shutil
import os
from datetime import datetime

router = APIRouter()

# Directory for saving mood logs
LOG_DIR = r"C:\Users\harik\smart-study-assistant-starter\smart-study-assistant-starter (2)\smart-study-assistant-starter\saved_files\mood_logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "mood_log.txt")

# Model for mood logging
class MoodEntry(BaseModel):
    mood: str
    emoji: str
    note: str
    timestamp: int

# Endpoint for mood detection
@router.post("/detect")
async def detect_mood(image: UploadFile = File(...)):
    try:
        temp_path = f"temp_{image.filename}"
        print(f"Saving image to {temp_path}")

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        print("Running DeepFace.analyze...")
        result = DeepFace.analyze(img_path=temp_path, actions=["emotion"], enforce_detection=False)
        print("DeepFace result:", result)

        mood = result[0]["dominant_emotion"]
        os.remove(temp_path)
        return {"mood": mood}

    except Exception as e:
        print("Error during mood detection:", e)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

# Endpoint to log mood
@router.post("/log")
async def log_mood(entry: MoodEntry):
    try:
        timestamp_str = datetime.fromtimestamp(entry.timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp_str} | {entry.emoji} {entry.mood} | {entry.note}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
        return {"message": "Mood logged successfully", "file_path": LOG_FILE}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log mood: {str(e)}")

# Endpoint to fetch saved mood logs
@router.get("/logs")
async def get_mood_logs():
    try:
        if not os.path.exists(LOG_FILE):
            return {"logs": []}
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        logs = [line.strip() for line in lines if line.strip()]
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")