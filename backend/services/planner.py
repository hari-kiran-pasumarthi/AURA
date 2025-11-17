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
    full_day_start = datetime.combine(for_date, dt_time(7, 0), IST)
    full_day_end = datetime.combine(for_date, dt_time(22, 30), IST)

    # start after "now" on first day
    if for_date == start_datetime.date():
        full_day_start = max(full_day_start, start_datetime + timedelta(minutes=5))

    busy_blocks = merge_busy_slots(DEFAULT_ROUTINE, existing_tasks.get(for_date, []))

    free = []
    pointer = full_day_start

    for b_start, b_end in busy_blocks:
        try:
            bs = datetime.combine(
                for_date, datetime.strptime(b_start, "%H:%M").time(), IST
            )
            be = datetime.combine(
                for_date, datetime.strptime(b_end, "%H:%M").time(), IST
            )
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
# MAIN PLANNER LOGIC — FULLY TIMEZONE-AWARE
# ------------------------------------------------------
def generate(req: PlannerRequest) -> PlannerResponse:
    # Make start_datetime timezone aware in IST
    start_dt = req.start_datetime
    if isinstance(start_dt, str):
        start_dt = datetime.fromisoformat(start_dt)

    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=IST)
    else:
        start_dt = start_dt.astimezone(IST)

    start_date = start_dt.date()

    # Planning horizon
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
    buckets: Dict[date, List[Dict[str, Any]]] = {
        start_date + timedelta(days=i): [] for i in range(horizon_days)
    }

    existing_tasks = load_existing_tasks()

    # --------------------------------------------------
    # Score tasks & normalize due datetime to IST
    # --------------------------------------------------
    scored_tasks = []
    for t in req.tasks:
        try:
            if isinstance(t.due, datetime):
                due_dt = t.due
            else:
                due_dt = datetime.fromisoformat(str(t.due))

            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=IST)
            else:
                due_dt = due_dt.astimezone(IST)

            due_date = due_dt.date()
            urgency = 1 / max(1, (due_date - start_date).days)
        except Exception:
            # fall back: treat as latest
            due_dt = datetime.combine(end_date, dt_time(23, 59), IST)
            urgency = 1

        est = float(t.estimated_hours or (t.difficulty * 1.5))
        score = urgency * t.difficulty
        # (score is kept only for logging/debug; sorting uses due_dt)
        scored_tasks.append((score, t, est, due_dt))

    # ✅ IMPORTANT: sort by earliest due datetime first, then by difficulty desc
    scored_tasks.sort(key=lambda x: (x[3], -x[1].difficulty))

    # --------------------------------------------------
    # Schedule tasks
    # --------------------------------------------------
    for score, task, remaining, due_dt in scored_tasks:
        current_day = start_date
        due_date = due_dt.date()
        due_time = due_dt.time()

        while remaining > 0 and current_day <= end_date:
            # Stop scheduling after due date
            if current_day > due_date:
                break

            used_today = sum(x["hours"] for x in buckets[current_day])
            if used_today >= daily_limit:
                current_day += timedelta(days=1)
                continue

            free_slots = get_free_slots(current_day, existing_tasks, start_dt)

            for fs, fe in free_slots:
                # On due-day: block times past due-time
                if current_day == due_date:
                    if fs.time() >= due_time:
                        continue
                    fe = min(fe, datetime.combine(current_day, due_time, IST))

                slot_duration = (fe - fs).total_seconds() / 3600
                if slot_duration <= 0:
                    continue

                available = min(slot_duration, daily_limit - used_today, remaining)
                if available <= 0:
                    continue

                end_time = fs + timedelta(hours=available)

                buckets[current_day].append(
                    {
                        "task": task.name,
                        "subject": task.subject,
                        "difficulty": task.difficulty,
                        "hours": round(available, 2),
                        "start_time": fs.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M"),
                        "due": due_dt.isoformat(),
                    }
                )

                remaining -= available
                used_today += available

            current_day += timedelta(days=1)

    # Build final schedule
    schedule = [
        {"date": d.isoformat(), "blocks": blocks}
        for d, blocks in buckets.items()
        if blocks
    ]

    # Save snapshot for future blocking
    try:
        save_dir = os.path.join("saved_files", "notes", "planner")
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
        data = {"schedule": schedule, "timestamp": datetime.now(IST).isoformat()}
        with open(
            os.path.join(save_dir, f"planner_{ts}.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    return PlannerResponse(schedule=schedule)
