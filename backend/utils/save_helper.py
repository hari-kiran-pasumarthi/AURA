import os, json
from datetime import datetime

# 🌍 Central directory for all Smart Study data
BASE_SAVE_DIR = "saved_data"
GLOBAL_LOG_FILE = os.path.join(BASE_SAVE_DIR, "smart_study_log.json")


def ensure_dir(path: str):
    """Ensure directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)


def _write_json(filepath: str, entry: dict):
    """Append an entry safely to a JSON file."""
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump([], f, indent=2)

    with open(filepath, "r+", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

        entry["timestamp"] = datetime.utcnow().isoformat()
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_data(module_name: str, filename: str, entry: dict):
    """
    Save an entry to a module's own file and the unified Smart Study log.
    Example: saved_data/autonote/saved_autonotes.json + smart_study_log.json
    """
    ensure_dir(BASE_SAVE_DIR)

    # 1️⃣ Save inside module folder
    module_dir = os.path.join(BASE_SAVE_DIR, module_name)
    ensure_dir(module_dir)
    filepath = os.path.join(module_dir, filename)
    _write_json(filepath, entry)

    # 2️⃣ Also add to unified Smart Study timeline
    unified_entry = {
        "module": module_name,
        "title": entry.get("title", f"{module_name.capitalize()} Entry"),
        "content": entry.get("summary", entry.get("text", entry.get("content", ""))),
        "metadata": entry.get("metadata", entry),
        "timestamp": datetime.utcnow().isoformat(),
    }
    _write_json(GLOBAL_LOG_FILE, unified_entry)

    print(f"✅ Saved entry for {module_name}: {unified_entry['title']}")


def save_entry(module: str, title: str, content: str, metadata: dict = None):
    """
    Convenience function to log any study-related event to the unified log.
    Automatically handled by all modules (AutoNote, Planner, Mood, etc.)
    """
    ensure_dir(BASE_SAVE_DIR)

    entry = {
        "module": module,
        "title": title,
        "content": content,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Save to global timeline only (for minor events)
    _write_json(GLOBAL_LOG_FILE, entry)
    print(f"🧠 Logged new study entry: {title} ({module})")
