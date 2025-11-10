from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import os, json
from datetime import datetime

# ------------------------------------
# Import routers for all your features
# ------------------------------------
from backend.routers import (
    auth,            # ✅ JSON-based Auth router
    autonote,
    focus,
    planner,
    doubts,
    flashcards,
    mood,
    distraction,
    timepredict,
    braindump,
    confusion,
    chatbot,
)

# ------------------
# Initialize FastAPI
# ------------------
app = FastAPI(title="The AURA", version="1.1.0")

# ---------------------------
# CORS Configuration
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aura-three-phi.vercel.app",  # your production frontend
        "http://localhost:8081",              # local frontend
        "http://localhost:3000",              # extra dev option
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Include Routers (AI + Auth modules)
# ---------------------------
app.include_router(auth.router)  # ✅ JSON-file-based auth
app.include_router(autonote.router)
app.include_router(focus.router)
app.include_router(planner.router)
app.include_router(doubts.router)
app.include_router(flashcards.router)
app.include_router(mood.router)
app.include_router(distraction.router, prefix="/distraction", tags=["DistractionSniper"])
app.include_router(timepredict.router)
app.include_router(braindump.router, prefix="/braindump", tags=["AutoSave BrainDump"])
app.include_router(confusion.router)
app.include_router(chatbot.router, prefix="/chatbot", tags=["ChatBot"])

# ---------------------------
# Root Route
# ---------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Smart Study Assistant API",
        "version": "1.1.0",
        "features": [
            "JSON-based Email Authentication",
            "Focus Tracker",
            "AutoNote Summarizer",
            "Planner",
            "Chatbot",
            "Dashboard",
        ],
    }

# ---------------------------
# Universal Saved Notes Route
# ---------------------------
@app.get("/notes/list/{module_name}")
async def universal_saved_notes(module_name: str):
    base_path = os.path.join(os.path.dirname(__file__), "backend", "saved_files")
    file_map = {
        "autonote": "autonote_notes/saved_autonotes.json",
        "planner": "planner_notes/saved_plans.json",
        "focus": "focus_notes/saved_focus.json",
        "flashcards": "flashcards_notes/saved_flashcards.json",
        "confusion": "confusion_notes/saved_confusion.json",
        "timepredict": "timepredict_notes/saved_timepredict.json",
    }

    if module_name not in file_map:
        return JSONResponse({"entries": []}, status_code=200)

    save_file_path = os.path.join(base_path, file_map[module_name])
    save_dir = os.path.dirname(save_file_path)
    os.makedirs(save_dir, exist_ok=True)

    if not os.path.exists(save_file_path):
        with open(save_file_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

    try:
        with open(save_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"entries": data}
    except Exception as e:
        return JSONResponse({"error": str(e), "entries": []}, status_code=500)

# ---------------------------
# Dashboard (for quick viewing)
# ---------------------------
@app.get("/dashboard", response_class=HTMLResponse)
async def unified_dashboard():
    SAVE_DIR = "saved_data"
    LOG_FILE = os.path.join(SAVE_DIR, "smart_study_log.json")

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    html = """
    <html>
    <head>
        <title>📊 Smart Study Assistant Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f9fafb; padding: 40px; color: #111827; }
            h1 { color: #1d4ed8; font-size: 30px; margin-bottom: 10px; }
            h2 { color: #2563eb; margin-top: 40px; }
            .entry { background: #f3f4f6; border-radius: 8px; padding: 12px 16px; margin-top: 10px; }
            .timestamp { color: #6b7280; font-size: 12px; margin-bottom: 5px; }
            .summary { color: #374151; margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>📘 Smart Study Assistant Dashboard</h1>
        <p>All saved session logs are listed below.</p>
    """

    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception as e:
            html += f"<p style='color:red;'>⚠️ Failed to read logs: {e}</p>"

    if not logs:
        html += "<p style='color:gray;'>No data found yet. Use any module to create entries.</p>"
    else:
        grouped = {}
        for log in logs:
            date_key = log.get("timestamp", "")[:10]
            grouped.setdefault(date_key, []).append(log)

        for date_key, entries in sorted(grouped.items(), reverse=True):
            html += f"<h2>📅 {date_key}</h2>"
            for entry in entries[::-1]:
                module = entry.get("module", "Unknown").capitalize()
                title = entry.get("title", "Untitled Entry")
                content = entry.get("content", "")
                timestamp = entry.get("timestamp", "")
                html += f"""
                <div class='entry'>
                    <div class='timestamp'>🧩 {module} | 🕒 {timestamp}</div>
                    <b>{title}</b>
                    <p class='summary'>{content}</p>
                </div>
                """

    html += "</body></html>"
    return HTMLResponse(content=html)

# ---------------------------
# Serve Frontend Build (if exists)
# ---------------------------
frontend_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "build"))
if os.path.isdir(frontend_build_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_build_dir, "static")), name="static")

    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def spa_index(request: Request, full_path: str):
        index_path = os.path.join(frontend_build_dir, "index.html")
        return FileResponse(index_path)
else:
    print(f"⚠️ React build directory not found at: {frontend_build_dir}")
