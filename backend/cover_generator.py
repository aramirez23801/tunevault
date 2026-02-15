import os
import base64
import uuid
import httpx
from openai import OpenAI
from fastapi import APIRouter, HTTPException, UploadFile, File
from db import get_connection
from auth import verify_api_key
from supabase import create_client

# ============================================================
# TuneVault — AI Cover Generator (3-Step Pipeline)
#
# Architecture:
#   Step 1: Playlist Analysis (GPT-4o, text-only)
#           → Analyzes each track title + artist individually
#           → Outputs structured mood, genre, color palette, visual themes
#
#   Step 2: Photo Description (GPT-4o, vision)
#           → Describes the uploaded photo in detail
#           → If photo is rejected, we skip and use playlist-only mode
#
#   Step 3: DALL-E Prompt Assembly (GPT-4o, text-only)
#           → Combines playlist analysis + photo description
#           → Produces a detailed, structured 250-300 word prompt
#           → DALL-E 3 generates the final image
#
#   Storage: Generated images are uploaded to Supabase Storage
#            for permanent URLs (DALL-E URLs expire after ~1 hour)
# ============================================================

router = APIRouter()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Supabase client for storage
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Supabase storage bucket name for covers
COVERS_BUCKET = "covers"


# ============================================================
# Helper: Upload image to Supabase Storage
# ============================================================

async def upload_to_supabase(image_url: str, playlist_id: int) -> str:
    """
    Downloads a DALL-E generated image and uploads it to Supabase Storage.
    Returns a permanent public URL.
    """
    # Download the image from DALL-E's temporary URL
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(image_url)
        image_bytes = response.content

    # Generate a unique filename
    filename = f"playlist_{playlist_id}/{uuid.uuid4().hex}.png"

    # Upload to Supabase Storage
    supabase.storage.from_(COVERS_BUCKET).upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": "image/png", "upsert": "true"}
    )

    # Get the permanent public URL
    supabase_url = os.getenv("SUPABASE_URL")
    public_url = f"{supabase_url}/storage/v1/object/public/{COVERS_BUCKET}/{filename}"

    return public_url


# ============================================================
# Step 1: Playlist Analysis (GPT-4o, text-only)
# ============================================================

def analyze_playlist(playlist_name: str, tracks: list) -> str:
    """
    Analyzes each track individually and produces a consolidated
    mood/visual description of the playlist. Uses GPT-4o's training
    knowledge to add context about known songs.
    """
    # Build detailed track list with numbering
    track_details = "\n".join([
        f"  {i+1}. \"{t[0]}\" by {t[1]}"
        for i, t in enumerate(tracks[:20])
    ])

    # Get unique artists
    artists = list(set([t[1] for t in tracks]))
    artist_list = ", ".join(artists[:10])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a music analyst and visual art director. Your job is to deeply analyze a music playlist and produce a rich visual description that could inspire album cover art.
                For EACH track in the playlist:
                1. What is the song about? (themes, emotions, story)
                2. What visual imagery does the song title and lyrics evoke?
                3. What colors and textures feel right for this song?
                
                Then CONSOLIDATE your findings into a unified playlist profile:
                - Overall genre and sub-genre
                - Dominant mood (e.g., melancholic, energetic, dreamy, aggressive)
                - Color palette (specific colors, not just "vibrant")
                - Visual themes (landscapes, urban, abstract, nature, etc.)
                - Art style that fits (photorealistic, oil painting, collage, watercolor, etc.)
                - Time of day / lighting (golden hour, midnight, overcast, etc.)
                - Texture and feel (gritty, smooth, rough, ethereal, etc.)
                
                Output your analysis as a structured description. Be SPECIFIC and UNIQUE to this playlist. Avoid generic descriptions."""
            },
            {
                "role": "user",
                "content": f"""Playlist: "{playlist_name}"
                Artists: {artist_list}
                Tracks:
                {track_details}
                Analyze each track, then give me a consolidated visual profile for this playlist."""
            }
        ],
        max_tokens=800
    )

    return response.choices[0].message.content.strip()


# ============================================================
# Step 2: Photo Description (GPT-4o, vision)
# ============================================================

def describe_photo(base64_image: str, content_type: str) -> str:
    """
    Analyzes the uploaded photo and produces a detailed description
    of its contents, composition, colors, and mood.
    Returns None if the photo is rejected by the API.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a visual analyst. Describe the uploaded photo in detail:
                    1. Main subject (what is it? animal, object, landscape, etc.)
                    2. Colors present (be specific: "burnt orange fur", not just "orange")
                    3. Setting/background
                    4. Composition (close-up, wide shot, centered, etc.)
                    5. Mood/feeling the photo evokes
                    6. Any notable textures or patterns
                    
                    Be descriptive but concise. Output ONLY the description, nothing else.
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this photo in detail for use in art direction."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Photo was rejected (e.g., copyright, real person, etc.)
        return None


# ============================================================
# Step 3: Assemble DALL-E Prompt (GPT-4o, text-only)
# ============================================================

def assemble_dalle_prompt(playlist_analysis: str, photo_description: str = None) -> str:
    """
    Combines the playlist analysis and photo description (if available)
    into a detailed, structured DALL-E 3 prompt.
    If no photo description, creates a prompt based purely on the music.
    """
    if photo_description:
        user_message = f"""PLAYLIST VISUAL PROFILE:
        {playlist_analysis}
        
        USER'S PHOTO DESCRIPTION: {photo_description}
        
        TASK: Create a detailed DALL-E image generation prompt that:
        1. Takes the main subject from the user's photo and reimagines it in an art style that matches the playlist's mood
        2. The scene, lighting, colors, and textures must all reflect the specific playlist analysis above
        3. The subject from the photo should be the focal point, placed in an environment inspired by the music
        4. Be extremely specific about colors (use the palette from the analysis), lighting, composition, and art style
        5. AVOID generic imagery. No "neon lights" or "vibrant cityscape" unless the analysis specifically calls for it"""
    else:
        user_message = f"""PLAYLIST VISUAL PROFILE: {playlist_analysis}
        
        NOTE: No user photo available. Create a standalone album cover.
        
        TASK: Create a detailed DALL-E image generation prompt that:
        1. Creates a compelling visual scene that perfectly captures the playlist's mood and themes
        2. The scene, lighting, colors, and textures must all reflect the specific playlist analysis above
        3. Choose a strong central subject or composition that represents the music's themes
        4. Be extremely specific about colors (use the palette from the analysis), lighting, composition, and art style
        5. AVOID generic imagery. No "neon lights" or "vibrant cityscape" unless the analysis specifically calls for it"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are an expert DALL-E prompt engineer. Write a single, detailed image generation prompt (250-300 words) for a square album cover.

                STRICT RULES:
                - Be EXTREMELY specific about: art style, color palette, lighting, composition, textures, and mood
                - Structure your prompt clearly: start with the main subject, then describe the environment, then the style/mood
                - The prompt must feel UNIQUE to this specific playlist — it should NOT work for any other playlist

                CRITICAL — DIFFERENTIATION:
                - Choose ONE dominant art style from the analysis (oil painting, watercolor, collage, photography, illustration, etc.) — do NOT blend multiple styles
                - Choose a SPECIFIC color palette of exactly 3-4 colors from the analysis — do NOT use every color mentioned
                - The scene setting must be SPECIFIC (e.g., "a desert highway at golden hour" not "an urban landscape") — pick the single strongest visual theme from the analysis
                - AVOID these overused DALL-E clichés: neon lights, rain-soaked streets, silhouettes with arms spread, cyberpunk cityscapes, floating elements, ethereal glows. Find MORE ORIGINAL compositions.
                - If the music is rock: think album covers like raw photography, bold graphic design, or gritty illustration — NOT fantasy art
                - If the music is pop: think clean, minimal, bright — NOT busy or dark
                - If the music is emotional/introspective: think intimate close-ups, natural landscapes, solitude — NOT crowded city scenes

                Output ONLY the prompt, nothing else."""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=500
    )

    return response.choices[0].message.content.strip()


# ============================================================
# Main Endpoint: Generate Cover
# ============================================================

@router.post("/playlists/{playlist_id}/generate-cover")
async def generate_cover(playlist_id: int, api_key: str, image: UploadFile = File(...)):
    """
    Generates an AI playlist cover using the 3-step pipeline:
    1. Analyze playlist tracks individually
    2. Describe the uploaded photo
    3. Combine both into a detailed DALL-E prompt
    4. Generate image with DALL-E 3
    5. Upload to Supabase Storage for permanent URL
    """
    user = verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()

    # Verify playlist belongs to user
    cur.execute(
        "SELECT playlist_id, name FROM playlists WHERE playlist_id = %s AND user_id = %s",
        (playlist_id, user["user_id"])
    )
    playlist = cur.fetchone()
    if playlist is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Playlist not found")

    playlist_name = playlist[1]

    # Get all tracks in the playlist
    cur.execute("""
        SELECT t.name, ar.name AS artist
        FROM playlist_tracks pt
        JOIN track t ON pt.track_id = t.track_id
        JOIN album a ON t.album_id = a.album_id
        JOIN artist ar ON a.artist_id = ar.artist_id
        WHERE pt.playlist_id = %s
    """, (playlist_id,))

    tracks = cur.fetchall()
    cur.close()
    conn.close()

    if len(tracks) == 0:
        raise HTTPException(status_code=400, detail="Playlist has no tracks. Add tracks before generating a cover.")

    # Read and encode the uploaded image
    image_bytes = await image.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    content_type = image.content_type or "image/jpeg"

    # ── Step 1: Analyze playlist tracks ──────────────────────
    playlist_analysis = analyze_playlist(playlist_name, tracks)

    # ── Step 2: Describe the uploaded photo ──────────────────
    photo_description = describe_photo(base64_image, content_type)

    # ── Step 3: Assemble the DALL-E prompt ───────────────────
    dalle_prompt = assemble_dalle_prompt(playlist_analysis, photo_description)

    # ── Step 4: Generate image with DALL-E 3 ─────────────────
    try:
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        temp_image_url = image_response.data[0].url
    except Exception:
        # Safety fallback: use playlist analysis without photo reference
        fallback_prompt = assemble_dalle_prompt(playlist_analysis, None)
        try:
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=fallback_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            temp_image_url = image_response.data[0].url
            dalle_prompt = fallback_prompt + " (fallback - no photo)"
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Image generation failed. Please try again."
            )

    # ── Step 5: Upload to Supabase Storage ───────────────────
    try:
        permanent_url = await upload_to_supabase(temp_image_url, playlist_id)
    except Exception:
        # If Supabase upload fails, return the temporary URL
        permanent_url = temp_image_url

    return {
        "message": "Cover generated",
        "image_url": permanent_url,
        "prompt_used": dalle_prompt,
        "playlist_analysis": playlist_analysis
    }


# ============================================================
# Save Cover URL to Database
# ============================================================

@router.put("/playlists/{playlist_id}/cover")
def save_cover(playlist_id: int, api_key: str, image_url: str):
    """Saves the generated cover URL to the playlist."""
    user = verify_api_key(api_key)

    conn = get_connection()
    cur = conn.cursor()

    # Verify playlist belongs to user
    cur.execute(
        "SELECT playlist_id FROM playlists WHERE playlist_id = %s AND user_id = %s",
        (playlist_id, user["user_id"])
    )
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Update cover URL
    cur.execute(
        "UPDATE playlists SET cover_image_url = %s WHERE playlist_id = %s",
        (image_url, playlist_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Cover saved"}