from fastapi import APIRouter
from ..models.schemas import TimePredictRequest, TimePredictResponse
from ..services import time_predictor

router = APIRouter()

@router.post("/predict", response_model=TimePredictResponse)
async def predict_time(req: TimePredictRequest):
    return time_predictor.train_and_predict(req)
