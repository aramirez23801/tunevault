import os
import hashlib
import secrets
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="TuneVault API", version="1.0.0")

# ============================================================
# Database helper
# ============================================================

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ============================================================
# Auth helper
# ============================================================

def verify_api_key(api_key: str):
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

# ============================================================
# Request body models
# ============================================================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# ============================================================
# Public endpoints
# ============================================================

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Welcome to TuneVault API"}

@app.post("/auth/register")
def register(user: RegisterRequest):
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

@app.post("/auth/login")
def login(user: LoginRequest):
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

# ============================================================
# Protected endpoints (require API key)
# ============================================================

@app.get("/me")
def get_me(api_key: str):
    user = verify_api_key(api_key)
    return {"message": "You are authenticated", "user": user}

# ============================================================
# Music catalog endpoints (coming next)
# ============================================================
@app.get("/tracks")
def get_tracks(api_key: str, limit: int = 20, offset: int = 0):
    verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.track_id, t.name, a.title AS album, ar.name AS artist, g.name AS genre,
               t.milliseconds, t.unit_price
        FROM track t
        JOIN album a ON t.album_id = a.album_id
        JOIN artist ar ON a.artist_id = ar.artist_id
        LEFT JOIN genre g ON t.genre_id = g.genre_id
        ORDER BY t.track_id
        LIMIT %s OFFSET %s
    """, (limit, offset))
    
    columns = [desc[0] for desc in cur.description]
    tracks = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()

    return {"count": len(tracks), "tracks": tracks}

@app.get("/tracks/{track_id}")
def get_track(track_id: int, api_key: str):
    verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.track_id, t.name, a.title AS album, ar.name AS artist, g.name AS genre,
               t.composer, t.milliseconds, t.bytes, t.unit_price
        FROM track t
        JOIN album a ON t.album_id = a.album_id
        JOIN artist ar ON a.artist_id = ar.artist_id
        LEFT JOIN genre g ON t.genre_id = g.genre_id
        WHERE t.track_id = %s
    """, (track_id,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result is None:
        raise HTTPException(status_code=404, detail="Track not found")

    columns = [desc[0] for desc in cur.description]
    return dict(zip(columns, result))

@app.get("/artists")
def get_artists(api_key: str, limit: int = 20, offset: int = 0):
    verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ar.artist_id, ar.name, COUNT(a.album_id) AS album_count
        FROM artist ar
        LEFT JOIN album a ON ar.artist_id = a.artist_id
        GROUP BY ar.artist_id, ar.name
        ORDER BY ar.name
        LIMIT %s OFFSET %s
    """, (limit, offset))

    columns = [desc[0] for desc in cur.description]
    artists = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()

    return {"count": len(artists), "artists": artists}

@app.get("/albums")
def get_albums(api_key: str, limit: int = 20, offset: int = 0, artist_id: int = None):
    verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()

    if artist_id:
        cur.execute("""
            SELECT a.album_id, a.title, ar.name AS artist
            FROM album a
            JOIN artist ar ON a.artist_id = ar.artist_id
            WHERE a.artist_id = %s
            ORDER BY a.title
            LIMIT %s OFFSET %s
        """, (artist_id, limit, offset))
    else:
        cur.execute("""
            SELECT a.album_id, a.title, ar.name AS artist
            FROM album a
            JOIN artist ar ON a.artist_id = ar.artist_id
            ORDER BY a.title
            LIMIT %s OFFSET %s
        """, (limit, offset))

    columns = [desc[0] for desc in cur.description]
    albums = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()

    return {"count": len(albums), "albums": albums}

@app.get("/genres")
def get_genres(api_key: str):
    verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT g.genre_id, g.name, COUNT(t.track_id) AS track_count
        FROM genre g
        LEFT JOIN track t ON g.genre_id = t.genre_id
        GROUP BY g.genre_id, g.name
        ORDER BY g.name
    """)

    columns = [desc[0] for desc in cur.description]
    genres = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()

    return {"count": len(genres), "genres": genres}