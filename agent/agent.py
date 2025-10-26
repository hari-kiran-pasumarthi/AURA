import time
import threading
import platform
import json
import requests
from datetime import datetime
from pynput import keyboard, mouse
import psutil

OS = platform.system().lower()
BACKEND_URL = "http://127.0.0.1:8000/focus/telemetry"
BATCH_SECONDS = 5  # send data every 5 seconds

keystrokes = 0
mouse_clicks = 0
last_input_time = time.time()
lock = threading.Lock()


def on_key_press(key):
    global keystrokes, last_input_time
    with lock:
        keystrokes += 1
        last_input_time = time.time()


def on_click(x, y, button, pressed):
    global mouse_clicks, last_input_time
    if pressed:
        with lock:
            mouse_clicks += 1
            last_input_time = time.time()


def get_active_window_name():
    try:
        if OS == "windows":
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd) or "unknown"
        elif OS == "darwin":
            from AppKit import NSWorkspace
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            return active_app.localizedName() or "unknown"
        else:
            return "unknown"
    except Exception:
        return "unknown"


def create_event():
    global keystrokes, mouse_clicks, last_input_time
    with lock:
        now = time.time()
        idle_seconds = now - last_input_time
        kpm = (keystrokes / BATCH_SECONDS) * 60
        event = {
            "timestamp": now,
            "app": get_active_window_name(),
            "is_study_app": False,
            "keys_per_min": round(kpm, 2),
            "mouse_clicks": mouse_clicks,
            "window_changes": 0,
            "idle_seconds": round(idle_seconds, 1),
        }
        keystrokes = 0
        mouse_clicks = 0
        return event


def sender_loop():
    while True:
        time.sleep(BATCH_SECONDS)
        event = create_event()
        app = event["app"].lower()
        study_keywords = ["vscode", "pycharm", "code", "notepad", "word", "pdf"]
        event["is_study_app"] = any(k in app for k in study_keywords)
        try:
            r = requests.post(BACKEND_URL, json=[event], timeout=5)
            print(f"[{datetime.now().isoformat()}] Sent: {event} (status {r.status_code})")
        except Exception as e:
            print(f"⚠️ Failed to send telemetry: {e}")


def start_agent():
    keyboard.Listener(on_press=on_key_press).start()
    mouse.Listener(on_click=on_click).start()

    threading.Thread(target=sender_loop, daemon=True).start()
    print(f"🧠 Focus Agent running... sending telemetry to {BACKEND_URL} every {BATCH_SECONDS}s")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Focus Agent stopped.")


if __name__ == "__main__":
    start_agent()
