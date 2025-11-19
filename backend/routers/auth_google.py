from fastapi import APIRouter, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
import jwt
import os
import json

router = APIRouter(prefix="/auth", tags=["Auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")

# Where user accounts are stored (same logic as your signup/login)
USERS_FILE = "saved_files/users.json"

# Ensure users file exists
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f, indent=2)


def create_or_get_user(email: str, name: str, picture: str):
    """
    Checks if the user exists in users.json, else creates a new one.
    Returns the user object.
    """
    with open(USERS_FILE, "r+", encoding="utf-8") as f:
        users = json.load(f)

        # Find user
        for user in users:
            if user["email"] == email:
                return user

        # If not found, create
        new_user = {
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.utcnow().isoformat(),
            "auth_method": "google"
        }

        users.append(new_user)
        f.seek(0)
        json.dump(users, f, indent=2)

        return new_user


@router.post("/google")
async def google_login(token: str):
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )

        email = idinfo["email"]
        name = idinfo.get("name", "AURA User")
        picture = idinfo.get("picture", "")

        # Ensure user exists in system
        user = create_or_get_user(email, name, picture)

        # Create AURA JWT
        payload = {
            "sub": email,
            "name": name,
            "picture": picture,
            "exp": datetime.utcnow() + timedelta(days=7)
        }

        jwt_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return {
            "access_token": jwt_token,
            "email": email,
            "name": name,
            "picture": picture
        }

    except Exception as e:
        print("GOOGLE LOGIN ERROR:", e)
        raise HTTPException(status_code=400, detail="Invalid Google Token")
