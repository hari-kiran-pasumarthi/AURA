import os, json
from datetime import datetime

# 🧭 Compute absolute base path (3 levels up from /backend/services/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 📁 Smart Study Calendar Directory
CALENDAR_DIR = os.path.join(BASE_DIR, "saved_files", "calendar")
CALENDAR_PATH = os.path.join(CALENDAR_DIR, "study_calendar.json")
os.makedirs(CALENDAR_DIR, exist_ok=True)


def load_calendar():
    """📚 Load saved study sessions from local Smart Calendar file."""
    if not os.path.exists(CALENDAR_PATH):
        with open(CALENDAR_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_to_calendar(schedule):
    """
    ✅ Save structured study schedule into Smart Study Calendar.
    Each block now includes start_time, end_time, difficulty, and due.
    """
    calendar = load_calendar()

    for day in schedule:
        for block in day.get("blocks", []):
            entry = {
                "date": day.get("date"),
                "task": block.get("task"),
                "subject": block.get("subject", "General"),
                "hours": block.get("hours"),
                "start_time": block.get("start_time"),
                "end_time": block.get("end_time"),
                "difficulty": block.get("difficulty", 3),
                "due": block.get("due"),
                "timestamp": datetime.utcnow().isoformat(),
            }
            calendar.append(entry)

    with open(CALENDAR_PATH, "w", encoding="utf-8") as f:
        json.dump(calendar, f, indent=2)

    return {"status": "success", "count": len(schedule)}


def list_calendar():
    """📅 Return all saved Smart Calendar entries."""
    data = load_calendar()
    return {"entries": data}


def clear_calendar():
    """🧹 Clear all saved Smart Calendar entries."""
    with open(CALENDAR_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)
    return {"status": "cleared"}
