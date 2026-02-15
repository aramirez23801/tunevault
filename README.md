# TuneVault — Music Catalog Explorer

A full-stack music catalog web application with AI-powered playlist cover generation. Browse 3,500+ tracks across 25 genres, create personalized playlists, and generate unique AI album covers by combining your photos with your playlist's musical vibe.

## Architecture

```
Frontend (Nginx)  →  Backend (FastAPI)  →  Database (Supabase/PostgreSQL)
                          ↓
                     OpenAI API (GPT-4o + DALL-E 3)
```

## Tech Stack

| Layer      | Technology                      |
| ---------- | ------------------------------- |
| Frontend   | HTML5, CSS3, Vanilla JavaScript |
| Backend    | Python 3.12, FastAPI, Uvicorn   |
| Database   | PostgreSQL (Supabase)           |
| Storage    | Supabase Storage                |
| AI Models  | OpenAI GPT-4o, DALL-E 3         |
| Containers | Docker (Nginx + Python)         |

## Features

- **Music Catalog** — Browse by genre, artist, or search by track name/artist
- **Playlist Management** — Create, delete, add/remove tracks
- **AI Cover Generation** — Upload a photo, GPT-4o analyzes your playlist's mood and your photo separately, then DALL-E 3 generates a unique cover combining both
- **User Authentication** — Register/login with API key-based sessions

## Setup & Installation

### Prerequisites

- Python 3.12+
- Docker
- Supabase account (database + storage)
- OpenAI API key

### Environment Variables

Create `backend/.env`:

```
DATABASE_URL=postgresql://user:pass@host:port/db
OPENAI_API_KEY=sk-your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### Local Development

**Backend:**

```bash
cd backend
pip install uv
uv sync
uv run fastapi dev main.py
# API available at http://127.0.0.1:8000
```

**Frontend:**

```bash
cd frontend
# Open index.html with VS Code Live Server
# or any static file server on port 5500
```

### Docker

```bash
# Backend
cd backend
docker build -t tunevault-backend .
docker run -p 8000:8000 --env-file .env tunevault-backend

# Frontend
cd frontend
docker build -t tunevault-frontend .
docker run -p 8080:80 tunevault-frontend
```

### Database Setup

The project uses the Chinook sample database hosted on Supabase. Additional tables required:

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE playlists (
    playlist_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    name VARCHAR(100) NOT NULL,
    cover_image_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE playlist_tracks (
    playlist_track_id SERIAL PRIMARY KEY,
    playlist_id INTEGER REFERENCES playlists(playlist_id) ON DELETE CASCADE,
    track_id INTEGER REFERENCES track(track_id),
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(playlist_id, track_id)
);
```

Supabase Storage: Create a public bucket named `covers` with SELECT and INSERT policies set to `true`.

## License

Academic project — Solutions Software Development course.
