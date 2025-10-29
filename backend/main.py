from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import os, json, time
from datetime import datetime
import requests

# -------------------------------
# Ollama remote connection config
# -------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "https://ollama-railway-hr3a.onrender.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")

def ensure_model_loaded(model_name=OLLAMA_MODEL):
    """Ensure Ollama model exists on the remote Render instance."""
    try:
        pull_url = f"{OLLAMA_URL}/api/pull"
        payload = {"model": model_name}
        print(f"🧠 Ensuring model '{model_name}' is available on Ollama at {OLLAMA_URL}...")
        r = requests.post(pull_url, json=payload, timeout=600)
        if r.status_code == 200:
            print(f"✅ Model '{model_name}' pull started/verified.")
        else:
            print(f"⚠️ Ollama returned {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Could not ensure model '{model_name}': {e}")

# ------------------------------------
# Import routers for all your features
# ------------------------------------
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

# ------------------
# Initialize FastAPI
# ------------------
app = FastAPI(title="The AURA", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aura-three-phi.vercel.app",  # your Vercel frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model on startup
@app.on_event("startup")
async def startup_event():
    ensure_model_loaded()

# Include routers
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

@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Smart Study Assistant API",
        "version": "1.0.0",
        "ollama_model": OLLAMA_MODEL,
        "ollama_url": OLLAMA_URL,
    }

# ---------------------------
# Dashboard and log rendering
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

# -------------------------------------
# Serve frontend React build (if exists)
# -------------------------------------
frontend_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "build"))

if os.path.isdir(frontend_build_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_build_dir, "static")), name="static")

    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def spa_index(request: Request, full_path: str):
        index_path = os.path.join(frontend_build_dir, "index.html")
        return FileResponse(index_path)
else:
    print(f"⚠️ React build directory not found at: {frontend_build_dir}")
