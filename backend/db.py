import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_connection():
    """Opens and returns a new connection to the Postgres database."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))