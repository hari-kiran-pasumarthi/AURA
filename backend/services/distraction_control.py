# backend/services/distraction_control_simple.py
import os
import shutil
import json
import psutil
from datetime import datetime

DATA_DIR = os.path.join(os.getenv("PROGRAMDATA", "C:\\ProgramData"), "distraction_blocker_simple")
os.makedirs(DATA_DIR, exist_ok=True)
MANIFEST = os.path.join(DATA_DIR, "state.json")

KEYWORDS = ["discord", "spotify", "netflix", "whatsapp", "tiktok", "youtube", "steam", "epic"]

def _load_state():
    try:
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"killed": [], "renamed": []}

def _save_state(state):
    state["timestamp"] = datetime.utcnow().isoformat()
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def find_running_matches(keywords=None):
    keywords = keywords or KEYWORDS
    matches = []
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            name = (proc.info.get("name") or "").lower()
            exe = proc.info.get("exe") or ""
            if any(k in name for k in keywords) or any(k in (exe or "").lower() for k in keywords):
                matches.append({"pid": proc.info["pid"], "name": proc.info["name"], "exe": exe})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return matches

def kill_processes(matches):
    killed = []
    for m in matches:
        try:
            p = psutil.Process(m["pid"])
            p.kill()
            killed.append(m)
        except Exception:
            continue
    state = _load_state()
    state["killed"] = state.get("killed", []) + killed
    _save_state(state)
    return killed

def find_exes_by_keywords(keywords=None, search_paths=None):
    keywords = keywords or KEYWORDS
    search_paths = search_paths or [r"C:\Program Files", r"C:\Program Files (x86)", os.path.expanduser(r"~\AppData\Local"), os.path.expanduser(r"~\AppData\Roaming")]
    found = []
    for base in search_paths:
        if not os.path.exists(base):
            continue
        for root, _, files in os.walk(base):
            for f in files:
                if f.lower().endswith(".exe"):
                    path = os.path.join(root, f)
                    low = path.lower()
                    if any(k in low for k in keywords):
                        found.append(path)
    return sorted(set(found))

def rename_exes_with_backup(paths):
    renamed = []
    for p in paths:
        try:
            if not os.path.exists(p):
                continue
            dirname = os.path.dirname(p)
            basename = os.path.basename(p)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            backup_name = f"{basename}.{timestamp}.bak"
            backup_path = os.path.join(DATA_DIR, backup_name)
            shutil.copy2(p, backup_path)
            blocked_name = basename + ".blocked"
            blocked_path = os.path.join(dirname, blocked_name)
            os.rename(p, blocked_path)
            renamed.append({"original": p, "backup": backup_path, "blocked": blocked_path})
        except Exception:
            continue
    state = _load_state()
    state["renamed"] = state.get("renamed", []) + renamed
    _save_state(state)
    return renamed

def restore_all():
    state = _load_state()
    restored = {"restored": [], "hosts_removed": []}
    for item in state.get("renamed", []):
        try:
            orig = item.get("original")
            backup = item.get("backup")
            blocked = item.get("blocked")
            if backup and os.path.exists(backup):
                shutil.copy2(backup, orig)
            if blocked and os.path.exists(blocked):
                try:
                    os.remove(blocked)
                except Exception:
                    pass
            restored["restored"].append(orig)
        except Exception:
            continue
    # clear manifest
    try:
        if os.path.exists(MANIFEST):
            os.remove(MANIFEST)
    except Exception:
        pass
    return restored