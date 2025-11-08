from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import json, os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "aura_super_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
USER_FILE = "users.json"

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize file storage
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump([], f)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def find_user(email: str):
    with open(USER_FILE, "r") as f:
        users = json.load(f)
    for u in users:
        if u["email"].lower() == email.lower():
            return u
    return None


# 🧩 Signup endpoint
@router.post("/signup")
async def signup(user: UserCreate):
    existing = find_user(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = {
        "email": user.email,
        "password": get_password_hash(user.password),
        "name": user.name,
        "created_at": datetime.utcnow().isoformat(),
    }

    with open(USER_FILE, "r+") as f:
        users = json.load(f)
        users.append(new_user)
        f.seek(0)
        json.dump(users, f, indent=2)

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user.email}


# 🔐 Login endpoint
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = find_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer", "user": user["email"]}


# ✅ Current user dependency
def get_current_user(token: str = Depends(OAuth2PasswordRequestForm)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = find_user(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
