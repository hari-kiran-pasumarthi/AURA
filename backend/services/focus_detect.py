from typing import List
from statistics import mean
from models.schemas import FocusEvent, FocusSuggestResponse
from utils.save_helper import save_entry  # ✅ Unified logger

# Apps considered productive/study-related
STUDY_APPS = {"code", "vscode", "pycharm", "word", "excel", "onenote", "pdf", "notepad", "chrome"}

def suggest(events: List[FocusEvent]) -> FocusSuggestResponse:
    """
    Analyze recent focus activity and log results to the unified timeline.
    """
    if not events:
        # ✅ Log empty data as well
        save_entry(
            module="focus",
            title="Focus Analysis Skipped",
            content="No focus events detected.",
            metadata={"events": []},
        )
        return FocusSuggestResponse(focused=False, suggest_pomodoro=True, reason="No events detected.")

    # Analyze last few minutes (up to 20 events)
    last_events = events[-min(20, len(events)):]
    kpm = mean([e.keys_per_min for e in last_events])
    clicks = mean([e.mouse_clicks for e in last_events])
    switches = mean([e.window_changes for e in last_events])
    study_ratio = sum(1 for e in last_events if e.is_study_app or e.app.lower() in STUDY_APPS) / len(last_events)

    # ✅ Corrected logic: suggest Pomodoro only if NOT focused
    focused = (kpm >= 80 or clicks >= 5) and switches <= 1 and study_ratio >= 0.7
    suggest = not focused

    reason = f"kpm={kpm:.1f}, clicks={clicks:.1f}, switches={switches:.1f}, study_ratio={study_ratio:.2f}"

    # ✅ Unified log entry
    try:
        save_entry(
            module="focus",
            title="Focus State Evaluated",
            content=("User is focused on study-related tasks." if focused else "User appears distracted or inactive."),
            metadata={
                "focused": focused,
                "suggest_pomodoro": suggest,
                "stats": {
                    "kpm": kpm,
                    "clicks": clicks,
                    "switches": switches,
                    "study_ratio": study_ratio,
                },
                "total_events": len(events),
            },
        )
    except Exception as e:
        print(f"⚠️ Failed to log focus analysis: {e}")

    return FocusSuggestResponse(focused=focused, suggest_pomodoro=suggest, reason=reason)
