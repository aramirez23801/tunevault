from pydantic import BaseModel

# Pydantic models define the expected structure of request bodies.
# FastAPI uses these to automatically validate incoming JSON data.

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class CreatePlaylistRequest(BaseModel):
    name: str

class AddTrackRequest(BaseModel):
    track_id: int
