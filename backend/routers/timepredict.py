from fastapi import APIRouter, HTTPException
from backend.models.schemas import TimePredictRequest, TimePredictResponse
from backend.services import time_predictor
from datetime import datetime
import os, json

router = APIRouter(prefix="/timepredict", tags=["StudyTime Predictor"])

SAVE_DIR = os.path.join("saved_data", "timepredict")
os.makedirs(SAVE_DIR, exist_ok=True)


@router.post("/predict", response_model=TimePredictResponse)
async def predict_time(req: TimePredictRequest):
    """⏳ Predict study time using trained model."""
    try:
        response = time_predictor.train_and_predict(req)

        # ✅ Auto-save result for Saved Folder
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_timepredict.json"
        path = os.path.join(SAVE_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(response.dict(), f, indent=2, ensure_ascii=False)

        return response
    except Exception as e:
        raise HTTPException(500, f"Time prediction failed: {e}")


@router.get("/saved")
async def get_saved_timepredict():
    """✅ Return all saved time predictions"""
    try:
        files = sorted(os.listdir(SAVE_DIR), reverse=True)
        entries = []
        for f in files:
            path = os.path.join(SAVE_DIR, f)
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                entries.append({
                    "id": os.path.basename(f).split("_")[0],
                    "title": "Study Time Prediction",
                    "content": data.get("predicted_time", "No prediction found"),
                    "timestamp": datetime.utcfromtimestamp(os.path.getmtime(path)).isoformat()
                })
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(500, f"Failed to load time predictions: {e}")

# ✅ Alias
@router.get("/notes/list/timepredict")
async def get_timepredict_alias():
    return await get_saved_timepredict()
