from backend.models.schemas import PlannerRequest, PlannerResponse
from datetime import date, timedelta, datetime, time as dt_time
from typing import List, Dict, Any, Tuple
from zoneinfo import ZoneInfo
import os, json

# ------------------------------------------------------
# Timezone (all internal datetimes will use IST)
# ------------------------------------------------------
IST = ZoneInfo("Asia/Kolkata")

# ------------------------------------------------------
# Default Routine (always fallback)
# ------------------------------------------------------
DEFAULT_ROUTINE = [
    {"label": "Wake Up", "start": "07:00", "end": "07:30", "type": "routine"},
    {"label": "Breakfast", "start": "08:00", "end": "08:30", "type": "meal"},
    {"label": "Lunch", "start": "13:00", "end": "14:00", "type": "meal"},
    {"label": "Evening Break", "start": "17:00", "end": "17:30", "type": "break"},
    {"label": "Dinner", "start": "20:00", "end": "20:30", "type": "meal"},
    {"label": "Sleep", "start": "22:30", "end": "07:00", "type": "sleep"},
]

# ------------------------------------------------------
# Load previous tasks to block slots
# ------------------------------------------------------
def load_existing_tasks() -> Dict[date, List[Tuple[str, str]]]:
    base_dir = os.path.join("saved_files", "notes", "planner")
    if not os.path.exists(base_dir):
        return {}

    booked = {}

    for fname in os.listdir(base_dir):
        if not fname.endswith(".json"):
            continue

        try:
            with open(os.path.join(base_dir, fname), "r") as f:
                data = json.load(f)

            for entry in data.get("schedule", []):
                try:
                    d = datetime.fromisoformat(entry["date"]).date()
                except:
                    continue

                for block in entry.get("blocks", []):
                    start = block.get("start_time")
                    end = block.get("end_time")
                    if start and end:
                        booked.setdefault(d, []).append((start, end))
        except:
            continue

    return booked


# ------------------------------------------------------
# Merge routine + existing busy slots
# ------------------------------------------------------
def merge_busy_slots(routine, existing):
    busy = [(r["start"], r["end"]) for r in routine]
    busy.extend(existing or [])
    busy.sort(key=lambda x: x[0])
    return busy


# ------------------------------------------------------
# Get free slots (24-hour)
# ------------------------------------------------------
def get_free_slots(for_date, routine, existing_tasks, start_datetime):
    full_day_start = datetime.combine(for_date, dt_time(0, 0), IST)
    full_day_end   = datetime.combine(for_date, dt_time(23, 59), IST)

    if for_date == start_datetime.date():
        full_day_start = max(full_day_start, start_datetime + timedelta(minutes=5))

    busy_blocks = merge_busy_slots(routine, existing_tasks.get(for_date, []))

    free = []
    pointer = full_day_start

    for b_start, b_end in busy_blocks:
        try:
            bs = datetime.combine(for_date, datetime.strptime(b_start, "%H:%M").time(), IST)
            be = datetime.combine(for_date, datetime.strptime(b_end, "%H:%M").time(), IST)
        except:
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
# MAIN PLANNER LOGIC
# ------------------------------------------------------
def generate(req: PlannerRequest, custom_routine=None) -> PlannerResponse:

    # Determine routine to use for THIS planning session only
    USER_ROUTINE = custom_routine or getattr(req, "routine", None) or DEFAULT_ROUTINE


    # Start datetime (IST-aware)
    start_dt = req.start_datetime
    if isinstance(start_dt, str):
        start_dt = datetime.fromisoformat(start_dt)

    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=IST)
    else:
        start_dt = start_dt.astimezone(IST)

    start_date = start_dt.date()

    # Planning window
    if req.end_date:
        end_dt = req.end_date
        if isinstance(end_dt, str):
            end_dt = datetime.fromisoformat(end_dt)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=IST)
        else:
            end_dt = end_dt.astimezone(IST)
        end_date = end_dt.date()
    else:
        end_date = start_date + timedelta(days=7)

    daily_limit = float(req.preferred_hours or 4)

    horizon_days = (end_date - start_date).days + 1
    buckets = {start_date + timedelta(days=i): [] for i in range(horizon_days)}

    existing_tasks = load_existing_tasks()

    # Score tasks + normalize due times
    scored = []
    for t in req.tasks:
        try:
            due_dt = datetime.fromisoformat(str(t.due))
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=IST)
            else:
                due_dt = due_dt.astimezone(IST)
        except:
            due_dt = datetime.combine(end_date, dt_time(23, 59), IST)

        urgency = 1 / max(1, (due_dt.date() - start_date).days)
        est = float(t.estimated_hours or (t.difficulty * 1.5))
        score = urgency * t.difficulty

        scored.append((score, t, est, due_dt))

    scored.sort(key=lambda x: (x[3], -x[1].difficulty))

    # Allocate tasks
    for score, task, remaining, due_dt in scored:
        current_day = start_date
        due_date = due_dt.date()
        due_time = due_dt.time()

        while remaining > 0 and current_day <= end_date:
            if current_day > due_date:
                break

            used_today = sum(x["hours"] for x in buckets[current_day])
            if used_today >= daily_limit:
                current_day += timedelta(days=1)
                continue

            free_slots = get_free_slots(current_day, USER_ROUTINE, existing_tasks, start_dt)

            for fs, fe in free_slots:

                if current_day == due_date:
                    if fs.time() >= due_time:
                        continue
                    fe = min(fe, datetime.combine(current_day, due_time, IST))

                slot_hours = (fe - fs).total_seconds() / 3600
                if slot_hours <= 0:
                    continue

                allocate = min(slot_hours, daily_limit - used_today, remaining)
                if allocate <= 0:
                    continue

                end_time = fs + timedelta(hours=allocate)

                buckets[current_day].append({
                    "task": task.name,
                    "subject": task.subject,
                    "difficulty": task.difficulty,
                    "hours": round(allocate, 2),
                    "start_time": fs.strftime("%H:%M"),
                    "end_time": end_time.strftime("%H:%M"),
                    "due": due_dt.isoformat(),
                })

                remaining -= allocate
                used_today += allocate

            current_day += timedelta(days=1)

    # Final schedule format
    schedule = [
        {"date": d.isoformat(), "blocks": blocks}
        for d, blocks in buckets.items()
        if blocks
    ]

    # Save snapshot INCLUDING ROUTINE
    try:
        save_dir = os.path.join("saved_files", "notes", "planner")
        os.makedirs(save_dir, exist_ok=True)

        ts = datetime.now(IST).strftime("%Y%m%d_%H%M%S")

        data = {
            "schedule": schedule,
            "tasks": [t.dict() for t in req.tasks],
            "routine": USER_ROUTINE,
            "timestamp": datetime.now(IST).isoformat(),
            "title": f"AI Study Plan - {ts}",
        }

        with open(os.path.join(save_dir, f"planner_{ts}.json"), "w") as f:
            json.dump(data, f, indent=2)

    except:
        pass

    return PlannerResponse(schedule=schedule)
