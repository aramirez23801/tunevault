import hashlib
import secrets
import psycopg2
from fastapi import APIRouter, HTTPException
from db import get_connection
from models import RegisterRequest, LoginRequest

# Router groups all authentication-related endpoints
router = APIRouter()

def verify_api_key(api_key: str):
    """Checks if the API key exists in the database and returns the user info."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, username FROM users WHERE api_key = %s",
        (api_key,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"user_id": user[0], "username": user[1]}

# --- Public endpoints ---

@router.post("/auth/register")
def register(user: RegisterRequest):
    """Creates a new user with a hashed password and unique API key."""
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    api_key = secrets.token_hex(32)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, api_key) VALUES (%s, %s, %s, %s)",
            (user.username, user.email, password_hash, api_key)
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    finally:
        cur.close()
        conn.close()

    return {"message": "User registered successfully", "api_key": api_key}

@router.post("/auth/login")
def login(user: LoginRequest):
    """Validates credentials and returns the user's API key."""
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, api_key FROM users WHERE email = %s AND password_hash = %s",
        (user.email, password_hash)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Login successful", "username": result[0], "api_key": result[1]}

# --- Protected endpoint ---

@router.get("/me")
def get_me(api_key: str):
    """Returns the authenticated user's info. Requires a valid API key."""
    user = verify_api_key(api_key)
    return {"message": "You are authenticated", "user": user}
