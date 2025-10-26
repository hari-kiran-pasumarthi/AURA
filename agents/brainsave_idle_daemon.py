"""
Idle detector -> pop a simple console prompt to dump thoughts.

This is intentionally simple for portability.
On heavy GUI systems you can swap with a proper tray app or Tkinter UI.
"""
import time, sys
from datetime import datetime
import os, json

IDLE_SECONDS = 300  # 5 minutes
LAST_ACTIVITY = time.time()

def activity_ping():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()

def record_dump(text):
    os.makedirs("data/brain_dumps", exist_ok=True)
    path = f"data/brain_dumps/{datetime.utcnow().isoformat()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"text": text, "ts": datetime.utcnow().isoformat()}, f, ensure_ascii=False, indent=2)
    print("Saved to", path)

def main():
    print("BrainDump idle daemon running. Press ENTER periodically here to simulate activity.", flush=True)
    while True:
        time.sleep(1)
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            _ = sys.stdin.readline()
            activity_ping()
        if time.time() - LAST_ACTIVITY > IDLE_SECONDS:
            print("\nYou've been idle. Brain dump your thoughts (empty to skip): ", end="", flush=True)
            txt = sys.stdin.readline().strip()
            if txt:
                record_dump(txt)
            activity_ping()

if __name__ == "__main__":
    import select
    main()
