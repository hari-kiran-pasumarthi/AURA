from backend.models.schemas import PlannerRequest, PlannerResponse
from datetime import date, timedelta, datetime, time
from typing import List, Dict, Any
import os, json

# ------------------------------------------------------
# 🕒 Default Blocked Routine
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
def load_existing_tasks():
  """
  Reads previous saved planner files from saved_files/notes/planner
  to block already scheduled sessions.
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


# ------------------------------------------------------
# Merge routine + existing busy slots
# ------------------------------------------------------
def merge_busy_slots(routine, existing):
  busy = [(r["start"], r["end"]) for r in routine if r["activity"].lower() != "sleep"]
  busy.extend(existing)
  busy.sort(key=lambda x: x[0])
  return busy


# ------------------------------------------------------
# Get free slots for a specific day
# ------------------------------------------------------
def get_free_slots(for_date, existing_tasks, start_datetime):
  full_day_start = datetime.combine(for_date, time(7, 0))
  full_day_end = datetime.combine(for_date, time(22, 30))

  # If this is the first day of planning, start *after now*
  if for_date == start_datetime.date():
      full_day_start = start_datetime + timedelta(minutes=5)

  busy = merge_busy_slots(DEFAULT_ROUTINE, existing_tasks.get(for_date, []))

  free = []
  pointer = full_day_start

  for b_start, b_end in busy:
      try:
          bs = datetime.combine(for_date, datetime.strptime(b_start, "%H:%M").time())
          be = datetime.combine(for_date, datetime.strptime(b_end, "%H:%M").time())
      except Exception:
          continue

      if bs > pointer:
          free.append((pointer, bs))

      if be > pointer:
          pointer = be

  if pointer < full_day_end:
      free.append((pointer, full_day_end))

  return free


# ==============================================================
# 🚀 MAIN PLANNER LOGIC — uses start_datetime (OPTION A)
# ==============================================================
def generate(req: PlannerRequest) -> PlannerResponse:
  print("🧠 Planner Started (Option A mode)")

  # ensure start_datetime is datetime
  start_dt: datetime = req.start_datetime
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
              due_date = datetime.fromisoformat(t.due).date()
          else:
              due_date = end_date

          days_left = max(1, (due_date - start_date).days)
          urgency = 1 / days_left
      except Exception:
          urgency = 1.0

      score = urgency * t.difficulty
      scored_tasks.append((score, t, hours))

  scored_tasks.sort(key=lambda x: x[0], reverse=True)
  print(f"🧾 {len(scored_tasks)} tasks sorted for scheduling (total ~{total_estimated:.1f} hrs).")

  # ------------------------------------------------------
  # Allocate tasks day-by-day
  # ------------------------------------------------------
  for score, task, remaining in scored_tasks:
      current_day = start_date

      while remaining > 0 and current_day <= end_date:
          used_today = sum(x["hours"] for x in buckets[current_day])
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

              buckets[current_day].append({
                  "task": task.name,
                  "subject": task.subject,
                  "difficulty": task.difficulty,
                  "hours": round(available, 2),
                  "start_time": fs.strftime("%H:%M"),
                  "end_time": end_time.strftime("%H:%M"),
                  "due": (
                      task.due.isoformat()
                      if isinstance(task.due, datetime)
                      else task.due
                  ),
              })

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

  # Optional: save a simple JSON so next runs can see existing sessions
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
