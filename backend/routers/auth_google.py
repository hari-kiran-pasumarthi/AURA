from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
import jwt
import os
import json

router = APIRouter(prefix="/auth", tags=["Auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")

USERS_FILE = "saved_files/users.json"
os.makedirs("saved_files", exist_ok=True)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f, indent=2)


# --------------------------
# Pydantic model to parse JSON
# --------------------------
class GoogleAuthRequest(BaseModel):
    token: str


# --------------------------
# Create or fetch user
# --------------------------
def create_or_get_user(email: str, name: str, picture: str):
    with open(USERS_FILE, "r+", encoding="utf-8") as f:
        users = json.load(f)

        for u in users:
            if u["email"] == email:
                return u

        new_user = {
            "email": email,
            "name": name,
            "picture": picture,
            "auth_method": "google",
            "created_at": datetime.utcnow().isoformat()
        }

        users.append(new_user)

        f.seek(0)
        json.dump(users, f, indent=2)

        return new_user


# --------------------------
# Google Login API
# --------------------------
@router.post("/google")
async def google_login(payload: GoogleAuthRequest):
    try:
        token = payload.token

        # Verify Google Token
        info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = info["email"]
        name = info.get("name", "AURA User")
        picture = info.get("picture", "")

        # Create or fetch user
        create_or_get_user(email, name, picture)

        # Create JWT
        jwt_token = jwt.encode(
            {
                "sub": email,
                "name": name,
                "picture": picture,
                "exp": datetime.utcnow() + timedelta(days=7)
            },
            JWT_SECRET,
            algorithm="HS256"
        )

        return {
            "access_token": jwt_token,
            "email": email,
            "name": name,
            "picture": picture
        }

    except Exception as e:
        print("GOOGLE LOGIN ERROR:", e)
        raise HTTPException(400, "Invalid Google Token")
