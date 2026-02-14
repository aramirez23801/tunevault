import psycopg2
from fastapi import APIRouter, HTTPException
from db import get_connection
from auth import verify_api_key
from models import CreatePlaylistRequest, AddTrackRequest

# Router groups all playlist-related endpoints
router = APIRouter()

@router.post("/playlists")
def create_playlist(playlist: CreatePlaylistRequest, api_key: str):
    """Creates a new playlist for the authenticated user."""
    user = verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO playlists (user_id, name) VALUES (%s, %s) RETURNING playlist_id, created_at",
        (user["user_id"], playlist.name)
    )
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Playlist created",
        "playlist_id": result[0],
        "name": playlist.name,
        "created_at": str(result[1])
    }

@router.get("/playlists")
def get_playlists(api_key: str):
    """Returns all playlists belonging to the authenticated user."""
    user = verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.playlist_id, p.name, p.created_at, COUNT(pt.track_id) AS track_count
        FROM playlists p
        LEFT JOIN playlist_tracks pt ON p.playlist_id = pt.playlist_id
        WHERE p.user_id = %s
        GROUP BY p.playlist_id, p.name, p.created_at
        ORDER BY p.created_at DESC
    """, (user["user_id"],))

    columns = [desc[0] for desc in cur.description]
    playlists = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()

    for p in playlists:
        p["created_at"] = str(p["created_at"])

    return {"count": len(playlists), "playlists": playlists}

@router.post("/playlists/{playlist_id}/tracks")
def add_track_to_playlist(playlist_id: int, track: AddTrackRequest, api_key: str):
    """Adds a track to a playlist. Verifies playlist ownership and track existence."""
    user = verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()

    # Verify the playlist belongs to this user
    cur.execute(
        "SELECT playlist_id FROM playlists WHERE playlist_id = %s AND user_id = %s",
        (playlist_id, user["user_id"])
    )
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Verify the track exists
    cur.execute("SELECT track_id FROM track WHERE track_id = %s", (track.track_id,))
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Track not found")

    # Add track to playlist
    try:
        cur.execute(
            "INSERT INTO playlist_tracks (playlist_id, track_id) VALUES (%s, %s)",
            (playlist_id, track.track_id)
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Track already in playlist")
    finally:
        cur.close()
        conn.close()

    return {"message": "Track added to playlist"}
