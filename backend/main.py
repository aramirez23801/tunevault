from fastapi import FastAPI
from auth import router as auth_router
from music import router as music_router
from playlists import router as playlists_router

app = FastAPI(title="TuneVault API", version="1.0.0")

# Register routers — each file handles its own group of endpoints
app.include_router(auth_router)
app.include_router(music_router)
app.include_router(playlists_router)

@app.get("/")
def health_check():
    """Public health check endpoint."""
    return {"status": "ok", "message": "Welcome to TuneVault API"}