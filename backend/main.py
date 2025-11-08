from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
from passlib.context import CryptContext
import os, json
from datetime import datetime, timedelta

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
app = FastAPI(title="The AURA", version="1.1.0")

# ---------------------------
# CORS Configuration
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aura-three-phi.vercel.app", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Database Setup (SQLite)
# ---------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./aura_users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------
# User Model
# ---------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# ---------------------------
# Auth Configuration
# ---------------------------
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_CHANGE_THIS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# ---------------------------
# AUTH ROUTES
# ---------------------------
@app.post("/auth/register")
def register_user(email: str, password: str, name: str = "", db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed_pw, name=name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "email": new_user.email}

@app.post("/auth/login")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "name": current_user.name}

@app.post("/auth/update-profile")
def update_profile(name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.name = name
    db.commit()
    return {"message": "Profile updated", "name": name}

# ---------------------------
# Include Routers (AI modules)
# ---------------------------
app.include_router(autonote.router)
app.include_router(focus.router)
app.include_router(planner.router)
app.include_router(doubts.router, prefix="/doubts", tags=["Silent Study Partner"])
app.include_router(flashcards.router)
app.include_router(mood.router, prefix="/mood", tags=["StudyMood Logger"])
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
            "Email Authentication",
            "Focus Tracker",
            "AutoNote",
            "Planner",
            "Chatbot",
            "Dashboard"
        ]
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
# Dashboard
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
