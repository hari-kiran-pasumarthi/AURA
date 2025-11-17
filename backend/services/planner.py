from backend.models.schemas import PlannerRequest, PlannerResponse
from datetime import date, timedelta, datetime, time as dt_time
from typing import List, Dict, Any, Tuple
import os, json

# ------------------------------------------------------
# 🕒 Default Blocked Routine (non-study time)
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
# 📂 Load Previous Tasks to Block Slots
# ------------------------------------------------------
def load_existing_tasks() -> Dict[date, List[Tuple[str, str]]]:
    """
    Reads previous saved planner files from saved_files/notes/planner
    and returns a dict: { date: [(start_time_str, end_time_str), ...], ... }
    These blocks will be treated as 'busy' when creating a new plan.
    """
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
            # ignore broken files quietly
            continue

    return booked


# ------------------------------------------------------
# Merge routine + existing busy slots
# ------------------------------------------------------
def merge_busy_slots(
    routine: List[Dict[str, str]], existing: List[Tuple[str, str]]
) -> List[Tuple[str, str]]:
    """
    Combine default routine (excluding sleep) with existing booked sessions.
    Returns a sorted list of (start_str, end_str) by time.
    """
    busy: List[Tuple[str, str]] = [
        (r["start"], r["end"])
        for r in routine
        if r.get("activity", "").lower() != "sleep"
    ]
    busy.extend(existing or [])

    # HH:MM string sort works as time sort
    busy.sort(key=lambda x: x[0])
    return busy


# ------------------------------------------------------
# Get free slots for a specific day
# ------------------------------------------------------
def get_free_slots(
    for_date: date,
    existing_tasks: Dict[date, List[Tuple[str, str]]],
    start_datetime: datetime,
) -> List[Tuple[datetime, datetime]]:
    """
    For a given date, return a list of (start_dt, end_dt) free slots
    between 07:00 and 22:30, excluding:
      - default routine (non-sleep)
      - already scheduled planner blocks (from old saved_files)
      - past time on the first day
    """
    full_day_start = datetime.combine(for_date, dt_time(7, 0))
    full_day_end = datetime.combine(for_date, dt_time(22, 30))

    # If this is the first day of planning, start *after now*
    if for_date == start_datetime.date():
        # small buffer so we don't schedule exactly at "now"
        full_day_start = max(full_day_start, start_datetime + timedelta(minutes=5))

    busy_blocks = merge_busy_slots(DEFAULT_ROUTINE, existing_tasks.get(for_date, []))

    free: List[Tuple[datetime, datetime]] = []
    pointer = full_day_start

    for b_start, b_end in busy_blocks:
        try:
            bs_time = datetime.strptime(b_start, "%H:%M").time()
            be_time = datetime.strptime(b_end, "%H:%M").time()
        except Exception:
            # ignore malformed times
            continue

        bs = datetime.combine(for_date, bs_time)
        be = datetime.combine(for_date, be_time)

        # if busy-block entirely before our pointer, ignore
        if be <= pointer:
            continue

        # gap between pointer and start of busy block
        if bs > pointer:
            free.append((pointer, bs))

        # move pointer to end of busy block
        pointer = max(pointer, be)

    # leftover gap until end of day
    if pointer < full_day_end:
        free.append((pointer, full_day_end))

    # filter out negative/zero slots
    free = [(s, e) for s, e in free if e > s]
    return free


# ==============================================================
# 🚀 MAIN PLANNER LOGIC — uses start_datetime
# ==============================================================
def generate(req: PlannerRequest) -> PlannerResponse:
    print("🧠 Planner Started (Option A mode)")

    # ensure start_datetime is datetime
    start_dt: datetime = req.start_datetime
    if isinstance(start_dt, str):
        # fallback in case something passes string from router
        start_dt = datetime.fromisoformat(start_dt)

    start_date = start_dt.date()
    print("⏰ Planning starts from:", start_dt.isoformat())

    # end_date window (defaults to +7 days if not provided)
    if req.end_date:
        end_date = req.end_date.date()
    else:
        end_date = start_date + timedelta(days=7)

    daily_limit = float(req.preferred_hours or 4)
    horizon_days = (end_date - start_date).days + 1

    buckets: Dict[date, List[Dict[str, Any]]] = {
        start_date + timedelta(days=i): [] for i in range(horizon_days)
    }

    # Load already scheduled tasks from previous planner runs
    existing_tasks = load_existing_tasks()
    print(f"📚 Existing booked days: {list(existing_tasks.keys())}")

    # ------------------------------------------------------
    # Score tasks by urgency × difficulty
    # ------------------------------------------------------
    scored_tasks = []
    total_estimated = 0.0

    for t in req.tasks:
        hours = float(t.estimated_hours or (t.difficulty * 1.5))
        total_estimated += hours

        # urgency calculation based on due date
        try:
            if isinstance(t.due, datetime):
                due_date = t.due.date()
            elif t.due:
                # handle ISO with or without offset
                due_dt = datetime.fromisoformat(str(t.due))
                due_date = due_dt.date()
            else:
                due_date = end_date

            days_left = max(1, (due_date - start_date).days)
            urgency = 1 / days_left
        except Exception:
            urgency = 1.0

        score = urgency * t.difficulty
        scored_tasks.append((score, t, hours))

    scored_tasks.sort(key=lambda x: x[0], reverse=True)
    print(
        f"🧾 {len(scored_tasks)} tasks sorted for scheduling "
        f"(total ~{total_estimated:.1f} hrs)."
    )

    # ------------------------------------------------------
    # Allocate tasks day-by-day
    # ------------------------------------------------------
    for score, task, remaining in scored_tasks:
    current_day = start_date

    # -------------------------------
    # ENFORCE HARD DUE DATE + TIME
    # -------------------------------
    try:
        # Task may come with full ISO datetime (date + time)
        if isinstance(task.due, datetime):
            due_dt = task.due
        else:
            due_dt = datetime.fromisoformat(str(task.due))
    except Exception:
        # fallback: if due invalid, allow all days
        due_dt = datetime.combine(end_date, dt_time(23, 59))

    due_date = due_dt.date()
    due_time = due_dt.time()

    # --------------------------------------------------------
    # Allocation loop
    # --------------------------------------------------------
    while remaining > 0 and current_day <= end_date:

        # ⛔ Rule 1 — DO NOT schedule after due DATE
        if current_day > due_date:
            print(f"⚠️ Stopping '{task.name}' because due date passed.")
            break

        used_today = sum(x["hours"] for x in buckets[current_day])
        if used_today >= daily_limit:
            current_day += timedelta(days=1)
            continue

        free_slots = get_free_slots(current_day, existing_tasks, start_dt)

        for fs, fe in free_slots:

            # ⛔ Rule 2 — If this is the due-day, do not exceed due TIME
            if current_day == due_date and fs.time() >= due_time:
                continue

            # Limit to due time if needed
            if current_day == due_date:
                fe = min(fe, datetime.combine(current_day, due_time))

            if remaining <= 0:
                break

            slot_duration = (fe - fs).seconds / 3600
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
                    "due": task.due.isoformat() if isinstance(task.due, datetime) else str(task.due),
                }
            )

            remaining -= available
            used_today += available

        current_day += timedelta(days=1)

            if used_today >= daily_limit:
                current_day += timedelta(days=1)
                continue

            free_slots = get_free_slots(current_day, existing_tasks, start_dt)

            for fs, fe in free_slots:
                if remaining <= 0:
                    break

                slot_duration = (fe - fs).seconds / 3600
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
                        "due": (
                            task.due.isoformat()
                            if isinstance(task.due, datetime)
                            else str(task.due)
                        ),
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

    print(f"✅ Planner generated {len(schedule)} day(s) of schedule.")

    # Snapshot for future blocking: saved_files/notes/planner
    try:
        save_dir = os.path.join("saved_files", "notes", "planner")
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        data = {
            "title": f"AI Study Plan - {ts}",
            "schedule": schedule,
            "timestamp": datetime.utcnow().isoformat(),
        }
        path = os.path.join(save_dir, f"planner_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Planner snapshot saved at {path}")
    except Exception as e:
        print(f"⚠️ Planner snapshot save failed: {e}")

    return PlannerResponse(schedule=schedule)
