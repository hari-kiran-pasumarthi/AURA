"""
Lightweight desktop focus monitor (cross-platform best-effort).

- Tracks keystrokes, clicks, and active window title.
- Buffers activity every 15 seconds and POSTS telemetry to FastAPI.
"""

import time, json, psutil, requests
from pynput import keyboard, mouse

K = 0
C = 0
W = 0
LAST_WINDOW = None
LAST_CHECK = time.time()

BACKEND_URL = "http://127.0.0.1:8000/focus/telemetry"  # ✅ make sure backend runs here

def on_press(key):
    global K
    K += 1

def on_click(x, y, button, pressed):
    global C
    if pressed:
        C += 1

def active_app_name():
    try:
        # Best-effort: get top CPU process name
        procs = sorted(
            psutil.process_iter(attrs=["name", "cpu_times"]),
            key=lambda p: sum(p.info.get("cpu_times")[:2]) if p.info.get("cpu_times") else 0,
            reverse=True,
        )
        if procs:
            return procs[0].info.get("name") or "unknown"
    except Exception:
        pass
    return "unknown"

def main():
    global K, C, W, LAST_WINDOW, LAST_CHECK
    kb = keyboard.Listener(on_press=on_press)
    ms = mouse.Listener(on_click=on_click)
    kb.start()
    ms.start()

    try:
        while True:
            time.sleep(15)
            now = time.time()
            app = active_app_name()

            if app != LAST_WINDOW:
                W += 1
                LAST_WINDOW = app

            kpm = (K / ((now - LAST_CHECK) / 60.0)) if now > LAST_CHECK else 0.0

            evt = {
                "timestamp": now,
                "app": app,
                "is_study_app": any(x in app.lower() for x in ["code", "word", "pdf", "notion", "pycharm", "chrome"]),
                "keys_per_min": kpm,
                "mouse_clicks": C,
                "window_changes": W,
            }

            # ✅ Send telemetry to backend
            try:
                res = requests.post(BACKEND_URL, json=[evt], timeout=5)
                if res.status_code == 200:
                    print(f"✅ Sent: {evt}")
                else:
                    print(f"⚠️ Backend responded {res.status_code}: {res.text}")
            except Exception as e:
                print(f"❌ Failed to send telemetry: {e}")

            # Reset counters
            K = 0
            C = 0
            W = 0
            LAST_CHECK = now

    except KeyboardInterrupt:
        print("🛑 Focus monitor stopped manually.")

if __name__ == "__main__":
    main()
