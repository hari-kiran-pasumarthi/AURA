import os, json, time
from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.schemas import DoubtEvent, DoubtReport
from backend.services import doubt_logger

router = APIRouter()

# Centralized saved files directory
SAVE_DIR = os.path.join("saved_files", "doubts")
os.makedirs(SAVE_DIR, exist_ok=True)


@router.post("/report", response_model=DoubtReport)
async def report_doubts(events: List[DoubtEvent]):
    """
    Analyze confusion signals and generate AI clarification.
    """
    return doubt_logger.report(events)


@router.post("/save")
async def save_doubt(entry: dict):
    """
    💾 Save AI clarification to saved_files/doubts/ as a .json file.
    """
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"doubt_{timestamp}.json"
        filepath = os.path.join(SAVE_DIR, filename)

        # Attach timestamp for reference
        entry["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)

        return {"status": "success", "file": filepath, "message": "Saved successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save doubt: {e}")


@router.get("/history")
async def list_saved_doubts():
    """
    📚 Return all saved doubts from saved_files/doubts/.
    """
    try:
        files = sorted(os.listdir(SAVE_DIR), reverse=True)
        data = []
        for fname in files:
            if fname.endswith(".json"):
                path = os.path.join(SAVE_DIR, fname)
                with open(path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    data.append({
                        "filename": fname,
                        "timestamp": content.get("timestamp", ""),
                        "topic": content.get("topic", "Unknown"),
                        "confidence": content.get("confidence", "N/A"),
                        "response": content.get("response", ""),
                    })
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load saved doubts: {e}")
