from backend.models.schemas import PlannerRequest, PlannerResponse
from datetime import date, timedelta, datetime
from typing import List, Dict, Any
import os, json
from backend.utils.save_helper import save_entry
from backend.services.smart_calendar import save_to_calendar

# 🕒 Default daily routine
DEFAULT_ROUTINE = [
    {"activity": "Wake Up", "start": "07:00", "end": "07:30"},
    {"activity": "Breakfast", "start": "08:00", "end": "08:30"},
    {"activity": "Lunch", "start": "13:00", "end": "14:00"},
    {"activity": "Evening Break", "start": "17:00", "end": "17:30"},
    {"activity": "Dinner", "start": "20:00", "end": "20:30"},
    {"activity": "Sleep", "start": "22:30", "end": "07:00"},
]


def load_existing_tasks() -> Dict[date, List[Dict[str, str]]]:
    """
    🔒 Load all previously scheduled planner sessions
    from saved_files/notes/planner/*.json to block those time slots.
    """
    base_dir = os.path.join("saved_files", "notes", "planner")
    if not os.path.exists(base_dir):
        return {}

    booked = {}
    for fname in os.listdir(base_dir):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(base_dir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("schedule", []):
                d = datetime.fromisoformat(entry["date"]).date()
                for block in entry.get("blocks", []):
                    booked.setdefault(d, []).append(
                        (block["start_time"], block["end_time"])
                    )
        except Exception:
            continue
    return booked


def merge_busy_slots(routine: List[Dict[str, str]], existing: List[tuple]) -> List[tuple]:
    """Merge default routine blocks and existing tasks into a single busy list."""
    busy = [(r["start"], r["end"]) for r in routine if r["activity"].lower() != "sleep"]
    busy.extend(existing)
    # Sort by start time
    busy.sort(key=lambda x: x[0])
    return busy


def get_free_slots(for_date: date, existing_tasks: Dict[date, List[tuple]]):
    """Return free slots for a date, excluding meals/sleep & previously booked tasks."""
    full_day_start = datetime.strptime("07:00", "%H:%M")
    full_day_end = datetime.strptime("22:30", "%H:%M")

    # If scheduling for today, start after current time
    now = datetime.now()
    if for_date == now.date():
        start_time = now + timedelta(minutes=5)
        full_day_start = datetime.strptime(start_time.strftime("%H:%M"), "%H:%M")

    # Merge routine and existing tasks
    busy = merge_busy_slots(DEFAULT_ROUTINE, existing_tasks.get(for_date, []))

    free = []
    pointer = full_day_start
    for b in busy:
        try:
            b_start = datetime.strptime(b[0], "%H:%M")
            b_end = datetime.strptime(b[1], "%H:%M")
        except Exception:
            continue

        if b_start > pointer:
            free.append((pointer.time(), b_start.time()))
        pointer = max(pointer, b_end)
    if pointer < full_day_end:
        free.append((pointer.time(), full_day_end.time()))
    return free


def generate(req: PlannerRequest) -> PlannerResponse:
    """
    🧩 Routine + Time-Aware Smart Planner
    -----------------------------------------
    ✅ Avoids meal/sleep hours
    ✅ Avoids previously scheduled sessions
    ✅ Starts from current time for same-day plans
    ✅ Compact plans stay single-day
    ✅ Logs & saves automatically
    """

    print("🧠 Starting planner generation...")

    # Step 1️⃣ — Setup planning window
    now = datetime.now()
    try:
        start = date.fromisoformat(req.start_date) if req.start_date else now.date()
    except Exception:
        start = now.date()

    try:
        end = date.fromisoformat(req.end_date) if req.end_date else (start + timedelta(days=7))
    except Exception:
        end = start + timedelta(days=7)

    daily_limit = float(req.daily_hours or 4)
    horizon_days = (end - start).days + 1
    buckets: Dict[date, List[Dict[str, Any]]] = {start + timedelta(days=i): [] for i in range(horizon_days)}

    print(f"📅 Planning from {start} → {end} ({horizon_days} days), daily limit: {daily_limit} hrs")

    # Step 2️⃣ — Validate tasks
    if not hasattr(req, "tasks") or not req.tasks:
        print("⚠️ No tasks found. Returning empty plan.")
        return PlannerResponse(schedule=[])

    # Step 3️⃣ — Load existing booked slots
    existing_tasks = load_existing_tasks()
    print(f"📚 Found {sum(len(v) for v in existing_tasks.values())} existing booked slots to avoid.")

    # Step 4️⃣ — Score tasks
    scored_tasks = []
    total_estimated_hours = 0
    for t in req.tasks:
        t_name = getattr(t, "name", "Untitled Task")
        t_subject = getattr(t, "subject", "General")
        t_due = getattr(t, "due", None)
        t_difficulty = getattr(t, "difficulty", 3)
        t_estimated = getattr(t, "estimated_hours", None)

        # Default estimation if not given
        total_hours = float(t_estimated or (t_difficulty * 1.5))
        total_estimated_hours += total_hours

        urgency = 1.0
        if t_due:
            try:
                if isinstance(t_due, datetime):
                    days_left = max(1, (t_due.date() - start).days)
                else:
                    due_date = datetime.fromisoformat(t_due)
                    days_left = max(1, (due_date.date() - start).days)
                urgency = 1 / days_left
            except Exception:
                urgency = 1.0

        score = urgency * t_difficulty
        scored_tasks.append((score, {
            "name": t_name,
            "subject": t_subject,
            "due": t_due,
            "difficulty": t_difficulty,
            "hours": total_hours
        }))

    scored_tasks.sort(key=lambda x: x[0], reverse=True)
    print(f"🧾 {len(scored_tasks)} tasks sorted by urgency × difficulty.")

    # Step 5️⃣ — Compact Plan Check
    if total_estimated_hours <= daily_limit:
        print(f"🕐 Compact plan: {total_estimated_hours:.1f}h ≤ {daily_limit}h → single day")
        end = start
        horizon_days = 1
        buckets = {start: []}

    # Step 6️⃣ — Schedule tasks
    for score, t in scored_tasks:
        remaining = t["hours"]
        try:
            if isinstance(t["due"], datetime):
                due_date = t["due"].date()
            elif t["due"]:
                due_date = datetime.fromisoformat(t["due"]).date()
            else:
                due_date = end
        except Exception:
            due_date = end

        current_day = start
        while remaining > 0 and current_day <= end:
            if current_day > due_date:
                break

            used_today = sum(x["hours"] for x in buckets[current_day])
            if used_today >= daily_limit:
                current_day += timedelta(days=1)
                continue

            free_slots = get_free_slots(current_day, existing_tasks)

            for slot in free_slots:
                if remaining <= 0:
                    break

                slot_start = datetime.combine(current_day, slot[0])
                slot_end = datetime.combine(current_day, slot[1])
                slot_duration = (slot_end - slot_start).seconds / 3600

                available = min(daily_limit - used_today, slot_duration, remaining)
                if available > 0:
                    end_time = slot_start + timedelta(hours=available)
                    buckets[current_day].append({
                        "task": t["name"],
                        "subject": t["subject"],
                        "hours": round(available, 2),
                        "start_time": slot_start.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M"),
                        "due": (
                            t["due"].isoformat() if isinstance(t["due"], datetime)
                            else (t["due"] or "N/A")
                        ),
                        "difficulty": t["difficulty"],
                    })
                    remaining -= available
                    used_today += available

            current_day += timedelta(days=1)

    # Step 7️⃣ — Build structured schedule
    schedule = [{"date": d.isoformat(), "blocks": blocks} for d, blocks in buckets.items() if blocks]
    print(f"✅ Generated {len(schedule)} day(s), total {total_estimated_hours:.1f} hrs.")

    # Step 8️⃣ — Save to Smart Calendar
    try:
        calendar_status = save_to_calendar(schedule)
        print(f"📆 Calendar updated ({calendar_status.get('count', 0)} days).")
    except Exception as e:
        print(f"⚠️ Calendar save failed: {e}")
        calendar_status = {"status": "failed"}

    # Step 9️⃣ — Log entry
    try:
        summary = f"Generated {len(schedule)} day plan with {len(req.tasks)} tasks."
        save_entry(
            module="planner",
            title="Smart Planner Executed",
            content=summary,
            metadata={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "task_count": len(req.tasks),
                "calendar_status": calendar_status,
            },
        )
    except Exception as e:
        print(f"⚠️ Logging failed: {e}")

    # 🔟 Save plan to disk
    try:
        save_dir = os.path.join("saved_files", "notes", "planner")
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        data = {
            "title": f"AI Study Plan - {ts}",
            "summary": f"{len(schedule)} days covering {len(req.tasks)} tasks.",
            "schedule": schedule,
            "timestamp": datetime.utcnow().isoformat(),
        }
        path = os.path.join(save_dir, f"planner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved planner at {path}")
    except Exception as e:
        print(f"⚠️ Save failed: {e}")

    return PlannerResponse(schedule=schedule)
