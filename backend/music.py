from fastapi import APIRouter, HTTPException
from db import get_connection
from auth import verify_api_key

# Router groups all music catalog endpoints
router = APIRouter()

@router.get("/tracks")
def get_tracks(api_key: str, limit: int = 20, offset: int = 0):
    """Returns a paginated list of tracks with album, artist, and genre info."""
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

@router.get("/tracks/search")
def search_tracks(api_key: str, q: str = None, genre: str = None, artist: str = None, limit: int = 20, offset: int = 0):
    """Search tracks by name, genre, or artist. All filters are optional and combinable."""
    verify_api_key(api_key)

    query = """
        SELECT t.track_id, t.name, a.title AS album, ar.name AS artist, g.name AS genre,
               t.milliseconds, t.unit_price
        FROM track t
        JOIN album a ON t.album_id = a.album_id
        JOIN artist ar ON a.artist_id = ar.artist_id
        LEFT JOIN genre g ON t.genre_id = g.genre_id
        WHERE 1=1
    """
    params = []

    if q:
        query += " AND (LOWER(t.name) LIKE %s OR LOWER(ar.name) LIKE %s)"
        params.extend([f"%{q.lower()}%", f"%{q.lower()}%"])

    if genre:
        query += " AND LOWER(g.name) = %s"
        params.append(genre.lower())

    if artist:
        query += " AND LOWER(ar.name) LIKE %s"
        params.append(f"%{artist.lower()}%")

    query += " ORDER BY t.name LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)

    columns = [desc[0] for desc in cur.description]
    tracks = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()

    return {"count": len(tracks), "tracks": tracks}

@router.get("/tracks/{track_id}")
def get_track(track_id: int, api_key: str):
    """Returns full details for a single track by ID."""
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

@router.get("/artists")
def get_artists(api_key: str, limit: int = 20, offset: int = 0):
    """Returns a paginated list of artists with their album count."""
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

@router.get("/albums")
def get_albums(api_key: str, limit: int = 20, offset: int = 0, artist_id: int = None):
    """Returns a paginated list of albums. Optionally filter by artist_id."""
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

@router.get("/genres")
def get_genres(api_key: str):
    """Returns all genres with the number of tracks in each."""
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
