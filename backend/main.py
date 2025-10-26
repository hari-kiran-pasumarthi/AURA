from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from backend.routers import (
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
import os, json, glob
from datetime import datetime

# ----------------------------------------------------
# 🚀 FastAPI Initialization
# ----------------------------------------------------
app = FastAPI(title="Smart Study Assistant API", version="1.0.0")

# 🌍 Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# 🔌 Include All Routers
# ----------------------------------------------------
app.include_router(autonote.router, prefix="/autonote", tags=["AutoNote AI"])
app.include_router(focus.router, prefix="/focus", tags=["FocusSense"])
app.include_router(planner.router, tags=["Planner"])
app.include_router(doubts.router, prefix="/doubts", tags=["Silent Study Partner"])
app.include_router(flashcards.router, prefix="/flashcards", tags=["MemoryVault"])
app.include_router(mood.router, prefix="/mood", tags=["StudyMood Logger"])
app.include_router(distraction.router, prefix="/distraction", tags=["DistractionSniper"])
app.include_router(timepredict.router, prefix="/time", tags=["StudyTime Predictor"])
app.include_router(braindump.router, prefix="/braindump", tags=["AutoSave BrainDump"])
app.include_router(confusion.router, prefix="/confusion", tags=["Concept Confusion Detector"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["ChatBot"])

# ----------------------------------------------------
# 🏠 Root Route
# ----------------------------------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Smart Study Assistant API",
        "version": "1.0.0",
        "dashboard": "/dashboard",
    }

@app.get("/favicon.ico")
async def favicon():
    return ""


# ----------------------------------------------------
# 📊 Smart Study Dashboard
# ----------------------------------------------------
@app.get("/dashboard", response_class=HTMLResponse)
async def unified_dashboard():
    """Simple browser view to check all module logs."""
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


# ----------------------------------------------------
# 🗂️ Universal Saved Notes Scanner
# ----------------------------------------------------
@app.get("/notes/list/{module}")
async def list_saved_notes(module: str):
    """
    🧠 Smart Study file scanner (final optimized version)
    Searches all possible directories for saved module data:
    ✅ saved_files/
    ✅ saved_data/
    ✅ backend/saved_data/
    """
    entries = []
    search_dirs = [
        "saved_files",             # new structure
        "saved_data",              # your current flashcard folder
        os.path.join("backend", "saved_data"),  # legacy support
    ]

    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue

        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".json") and module.lower() in file.lower():
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                entries.append(data)
                            elif isinstance(data, list):
                                entries.extend(data)
                        print(f"✅ Loaded: {file_path}")
                    except Exception as e:
                        print(f"⚠️ Failed to read {file_path}: {e}")

    # Add timestamp if missing
    for entry in entries:
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.utcnow().isoformat()

    # Sort newest first
    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    print(f"📦 Total entries found for '{module}': {len(entries)}")
    return {"entries": entries}
