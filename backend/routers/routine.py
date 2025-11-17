from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.routers.auth import get_current_user
import os, json

router = APIRouter(prefix="/routine", tags=["Routine"])

class RoutineItem(BaseModel):
    label: str
    start: str
    end: str
    type: str

class RoutineRequest(BaseModel):
    items: list[RoutineItem]

def user_routine_path(email: str):
    base = os.path.join("saved_files", "users", email)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "routine.json")


@router.post("/save")
def save_user_routine(req: RoutineRequest, current_user=Depends(get_current_user)):
    path = user_routine_path(current_user)
    
    with open(path, "w") as f:
        json.dump(req.dict(), f, indent=2)
    
    return {"ok": True, "saved": True}


@router.get("/load")
def load_user_routine(current_user=Depends(get_current_user)):
    path = user_routine_path(current_user)

    if not os.path.exists(path):
        return {"items": []}

    with open(path, "r") as f:
        return json.load(f)
