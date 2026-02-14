import os
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title="TuneVault API", version="1.0.0")

def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        yield conn
    finally:
        conn.close()

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Welcome to TuneVault API"}

@app.get("/test-db")
def test_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM track")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"tracks_in_database": count}