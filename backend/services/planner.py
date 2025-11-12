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


def generate(req: PlannerRequest) -> PlannerResponse:
    """
    🧩 Routine-Aware Smart Planner (Improved)
    -----------------------------------------
    ✅ Respects short tasks (≤ daily_hours)
    ✅ Uses due datetime (not just date)
    ✅ Avoids multi-day plans unless needed
    ✅ Keeps existing calendar + logging flow
    """

    print("🧠 Starting planner generation...")

    # Step 1️⃣ — Setup planning window
    try:
        start = date.fromisoformat(req.start_date) if req.start_date else date.today()
    except Exception:
        start = date.today()

    try:
        end = date.fromisoformat(req.end_date) if req.end_date else (start + timedelta(days=7))
    except Exception:
        end = start + timedelta(days=7)

    horizon_days = (end - start).days + 1
    daily_limit = float(req.daily_hours or 4)
    buckets: Dict[date, List[Dict[str, Any]]] = {start + timedelta(days=i): [] for i in range(horizon_days)}

    print(f"📅 Planning from {start} to {end} ({horizon_days} days), daily limit: {daily_limit} hrs")

    # Step 2️⃣ — Validate tasks
    if not hasattr(req, "tasks") or not req.tasks:
        print("⚠️ No tasks found in request. Generating empty planner.")
        return PlannerResponse(schedule=[])

    # Step 3️⃣ — Score tasks
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
                # ⏰ Support datetime (not just date)
                if isinstance(t_due, datetime):
                    days_left = max(1, (t_due.date() - start).days)
                else:
                    due_date = datetime.fromisoformat(t_due)
                    days_left = max(1, (due_date.date() - start).days)
                urgency = 1 / days_left
            except Exception:
                urgency = 1.0

        score = urgency * t_difficulty
        scored_tasks.append(
            (score, {
                "name": t_name,
                "subject": t_subject,
                "due": t_due,
                "difficulty": t_difficulty,
                "hours": total_hours
            })
        )

    scored_tasks.sort(key=lambda x: x[0], reverse=True)
    print(f"🧾 Found {len(scored_tasks)} tasks, prioritized by urgency × difficulty.")

    # ✅ Step 3.5 — Detect short plans
    if total_estimated_hours <= daily_limit:
        print(f"🕐 All tasks fit within one day ({total_estimated_hours:.1f} hrs ≤ {daily_limit} hrs).")
        end = start
        horizon_days = 1
        buckets = {start: []}

    # Step 4️⃣ — Define available time slots (excluding meals)
    def get_free_slots():
        full_day_start = datetime.strptime("07:00", "%H:%M")
        full_day_end = datetime.strptime("22:30", "%H:%M")
        busy = [(r["start"], r["end"]) for r in DEFAULT_ROUTINE if r["activity"].lower() != "sleep"]

        free = []
        pointer = full_day_start
        for b in busy:
            b_start = datetime.strptime(b[0], "%H:%M")
            b_end = datetime.strptime(b[1], "%H:%M")
            if b_start > pointer:
                free.append((pointer.time(), b_start.time()))
            pointer = b_end
        if pointer < full_day_end:
            free.append((pointer.time(), full_day_end.time()))
        return free

    free_slots = get_free_slots()
    print(f"🕒 Available free slots per day: {len(free_slots)}")

    # Step 5️⃣ — Assign tasks to slots
    for score, t in scored_tasks:
        remaining = t["hours"]

        # Use datetime if due provided
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

    # Step 6️⃣ — Build structured schedule
    schedule = [{"date": d.isoformat(), "blocks": blocks} for d, blocks in buckets.items() if blocks]
    print(f"✅ Generated {len(schedule)} day(s) of structured schedule ({total_estimated_hours:.1f} hrs total).")

    # Step 7️⃣ — Save to Smart Calendar
    try:
        calendar_status = save_to_calendar(schedule)
        print(f"📆 Smart Calendar updated ({calendar_status.get('count', 0)} days).")
    except Exception as e:
        print(f"⚠️ Calendar save failed: {e}")
        calendar_status = {"status": "failed", "count": 0}

    # Step 8️⃣ — Log to unified timeline
    try:
        summary = f"Generated {len(schedule)} study days with {len(req.tasks)} tasks."
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
        print("🗂️ Planner log entry saved.")
    except Exception as e:
        print(f"⚠️ Logging failed: {e}")

    # Step 9️⃣ — Save the full plan to disk
    try:
        save_dir = os.path.join("saved_files", "notes", "planner")
        os.makedirs(save_dir, exist_ok=True)
        timestamp_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        file_data = {
            "title": f"AI Study Plan - {timestamp_now}",
            "summary": f"📅 {len(schedule)} days planned covering {len(req.tasks)} tasks.",
            "content": f"Tasks: {', '.join([t['name'] for _, t in scored_tasks]) or 'No tasks'}",
            "schedule": schedule,
            "timestamp": datetime.utcnow().isoformat(),
        }
        save_path = os.path.join(save_dir, f"planner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Full planner schedule saved at {save_path}")
    except Exception as e:
        print(f"⚠️ Failed to save full planner schedule: {e}")

    # ✅ Step 🔟 — Return structured response
    return PlannerResponse(schedule=schedule)
