from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ---------- Autonote ----------
class TranscriptRequest(BaseModel):
    text: Optional[str] = None
    emphasize_keywords: List[str] = Field(default_factory=lambda: ["important", "focus", "key point", "remember"])

class TranscriptResponse(BaseModel):
    summary: str
    highlights: List[str]
    bullets: List[str]

# ---------- Focus ----------
class FocusEvent(BaseModel):
    timestamp: float
    app: str
    is_study_app: bool
    keys_per_min: float
    mouse_clicks: int
    window_changes: int

class FocusSuggestResponse(BaseModel):
    focused: bool
    suggest_pomodoro: bool
    reason: str

# ---------- Planner ----------
class Task(BaseModel):
    name: str
    due: Optional[str] = None
    difficulty: int = 3  # 1-5 scale
    estimated_hours: Optional[float] = None
    subject: Optional[str] = None

class PlannerRequest(BaseModel):
    tasks: List[Task]
    daily_hours: float = 4.0
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None

class PlannerResponse(BaseModel):
    schedule: List[Dict[str, Any]]

# ---------- Doubt Solver ----------
class DoubtEvent(BaseModel):
    timestamp: float
    event: str  # e.g., "tab_switch", "scroll_up", "pause", "rewind"
    context: Optional[str] = None

class DoubtReport(BaseModel):
    topics: List[str]
    notes: List[str]

# ---------- Flashcards ----------
class FlashcardRequest(BaseModel):
    text: Optional[str] = None
    pdf_path: Optional[str] = None
    num: int = 20
    tags: Optional[List[str]] = None

class Flashcard(BaseModel):
    q: str
    a: str
    tags: List[str] = []

class FlashcardResponse(BaseModel):
    cards: List[Flashcard]

# ---------- Mood Tracker ----------
class MoodEvent(BaseModel):
    mood: str               # e.g., "Happy"
    emoji: str              # e.g., "😄"
    note: Optional[str] = None
    timestamp: Optional[float] = None  # Unix timestamp

# ---------- Distraction Blocker ----------
class DistractionConfig(BaseModel):
    blocked_apps: List[str] = Field(default_factory=lambda: ["instagram", "tiktok", "youtube", "steam"])

# ---------- Time Predictor ----------
class TimeRecord(BaseModel):
    features: List[float]
    duration_minutes: float

class TimePredictRequest(BaseModel):
    X: List[List[float]]
    y: List[float]
    X_future: List[List[float]]

class TimePredictResponse(BaseModel):
    y_pred: List[float]

# ---------- Brain Dump ----------
class BrainDump(BaseModel):
    text: str
    tags: List[str] = []

# ---------- Confusion Tracker ----------
class ConfusionRequest(BaseModel):
    text: str

class ConfusionResponse(BaseModel):
    unclear_spans: List[str]
    suggestions: List[str]