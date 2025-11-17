from backend.models.schemas import PlannerRequest, PlannerResponse
from datetime import date, timedelta, datetime, time as dt_time
from typing import List, Dict, Any, Tuple
import os, json

# ------------------------------------------------------
# Default Blocked Routine
# ------------------------------------------------------
DEFAULT_ROUTINE = [
    {"activity": "Wake Up", "start": "07:00", "end": "07:30"},
    {"activity": "Breakfast", "start": "08:00", "end": "08:30"},
    {"activity": "Lunch", "start": "13:00", "end": "14:00"},
    {"activity": "Evening Break", "start": "17:00", "end": "17:30"},
    {"activity": "Dinner", "start": "20:00", "end": "20:30"},
    {"activity": "Sleep", "start": "22:30", "end": "07:00"},
]


# ------------------------------------------------------
# Load previous tasks to block slots
# ------------------------------------------------------
def load_existing_tasks() -> Dict[date, List[Tuple[str, str]]]:
    base_dir = os.path.join("saved_files", "notes", "planner")
    if not os.path.exists(base_dir):
        return {}

    booked: Dict[date, List[Tuple[str, str]]] = {}

    for fname in os.listdir(base_dir):
        if not fname.endswith(".json"):
            continue

        try:
            with open(os.path.join(base_dir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)

            for entry in data.get("schedule", []):
                try:
                    d = datetime.fromisoformat(entry["date"]).date()
                except Exception:
                    continue

                for block in entry.get("blocks", []):
                    start_str = block.get("start_time")
                    end_str = block.get("end_time")
                    if not start_str or not end_str:
                        continue

                    booked.setdefault(d, []).append((start_str, end_str))
        except Exception:
            continue

    return booked


# ------------------------------------------------------
# Merge routine and existing busy slots
# ------------------------------------------------------
def merge_busy_slots(routine, existing):
    busy = [
        (r["start"], r["end"])
        for r in routine
        if r.get("activity", "").lower() != "sleep"
    ]
    busy.extend(existing or [])
    busy.sort(key=lambda x: x[0])
    return busy


# ------------------------------------------------------
# Find free slots for a specific day
# ------------------------------------------------------
def get_free_slots(for_date, existing_tasks, start_datetime):
    full_day_start = datetime.combine(for_date, dt_time(7, 0))
    full_day_end = datetime.combine(for_date, dt_time(22, 30))

    if for_date == start_datetime.date():
        full_day_start = max(full_day_start, start_datetime + timedelta(minutes=5))

    busy_blocks = merge_busy_slots(DEFAULT_ROUTINE, existing_tasks.get(for_date, []))

    free = []
    pointer = full_day_start

    for b_start, b_end in busy_blocks:
        try:
            bs = datetime.combine(for_date, datetime.strptime(b_start, "%H:%M").time())
            be = datetime.combine(for_date, datetime.strptime(b_end, "%H:%M").time())
        except Exception:
            continue

        if be <= pointer:
            continue

        if bs > pointer:
            free.append((pointer, bs))

        pointer = max(pointer, be)

    if pointer < full_day_end:
        free.append((pointer, full_day_end))

    return [(s, e) for s, e in free if e > s]


# ------------------------------------------------------
# MAIN PLANNER LOGIC — WITH HARD DUE DATE AND TIME
# ------------------------------------------------------
def generate(req: PlannerRequest) -> PlannerResponse:
    start_dt = req.start_datetime
    if isinstance(start_dt, str):
        start_dt = datetime.fromisoformat(start_dt)

    start_date = start_dt.date()

    if req.end_date:
        end_date = req.end_date.date()
    else:
        end_date = start_date + timedelta(days=7)

    daily_limit = float(req.preferred_hours or 4)
    horizon_days = (end_date - start_date).days + 1

    buckets: Dict[date, List[Dict[str, Any]]] = {
        start_date + timedelta(days=i): []
        for i in range(horizon_days)
    }

    existing_tasks = load_existing_tasks()

    # Score tasks
    scored_tasks = []
    for t in req.tasks:
        try:
            if isinstance(t.due, datetime):
                due_date = t.due.date()
            else:
                due_date = datetime.fromisoformat(str(t.due)).date()
            urgency = 1 / max(1, (due_date - start_date).days)
        except:
            urgency = 1

        est = float(t.estimated_hours or (t.difficulty * 1.5))
        score = urgency * t.difficulty
        scored_tasks.append((score, t, est))

    scored_tasks.sort(key=lambda x: x[0], reverse=True)

    # Allocate tasks
    for score, task, remaining in scored_tasks:
        current_day = start_date

        # Parse due datetime fully (date + time)
        try:
            if isinstance(task.due, datetime):
                due_dt = task.due
            else:
                due_dt = datetime.fromisoformat(str(task.due))
        except:
            due_dt = datetime.combine(end_date, dt_time(23, 59))

        due_date = due_dt.date()
        due_time = due_dt.time()

        while remaining > 0 and current_day <= end_date:

            # Stop if date passed
            if current_day > due_date:
                break

            used_today = sum(x["hours"] for x in buckets[current_day])
            if used_today >= daily_limit:
                current_day += timedelta(days=1)
                continue

            free_slots = get_free_slots(current_day, existing_tasks, start_dt)

            for fs, fe in free_slots:

                # If due-day, block times past due_time
                if current_day == due_date:
                    if fs.time() >= due_time:
                        continue
                    fe = min(fe, datetime.combine(current_day, due_time))

                slot_duration = (fe - fs).seconds / 3600
                if slot_duration <= 0:
                    continue

                available = min(slot_duration, daily_limit - used_today, remaining)
                if available <= 0:
                    continue

                end_time = fs + timedelta(hours=available)

                buckets[current_day].append({
                    "task": task.name,
                    "subject": task.subject,
                    "difficulty": task.difficulty,
                    "hours": round(available, 2),
                    "start_time": fs.strftime("%H:%M"),
                    "end_time": end_time.strftime("%H:%M"),
                    "due": str(task.due),
                })

                remaining -= available
                used_today += available

            current_day += timedelta(days=1)

    # Build schedule output
    schedule = [
        {"date": d.isoformat(), "blocks": blocks}
        for d, blocks in buckets.items()
        if blocks
    ]

    # Save snapshot for future blocking
    try:
        save_dir = os.path.join("saved_files", "notes", "planner")
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        data = {"schedule": schedule, "timestamp": datetime.utcnow().isoformat()}
        with open(os.path.join(save_dir, f"planner_{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except:
        pass

    return PlannerResponse(schedule=schedule)
