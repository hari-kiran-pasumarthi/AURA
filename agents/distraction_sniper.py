"""
Kill configured distracting apps now and keep watching every 30s.
"""
import time, json, os, psutil

CFG_PATH = "data/distraction_config.json"
os.makedirs("data", exist_ok=True)

def load_blocked():
    if not os.path.exists(CFG_PATH):
        return ["instagram", "tiktok", "youtube", "steam"]
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return [a.lower() for a in json.load(f).get("blocked_apps", [])]

def nuke_once(blocked):
    killed = []
    for p in psutil.process_iter(attrs=["name"]):
        name = (p.info.get("name") or "").lower()
        if any(b in name for b in blocked):
            try:
                p.terminate()
                killed.append(name)
            except Exception:
                pass
    if killed:
        print("Killed:", killed, flush=True)

def main():
    while True:
        blocked = load_blocked()
        nuke_once(blocked)
        time.sleep(30)

if __name__ == "__main__":
    main()
