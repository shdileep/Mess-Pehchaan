import sys
import os
import psycopg2

# Path to the virtual environment packages
VENV_PACKAGES = r"D:\Mess Pehchaan\mess-pehchaan\.venv\Lib\site-packages"

# Ensure venv packages are available to import deepface, retinaface, etc.
if VENV_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_PACKAGES) # Use insert(0, ...) to prioritize this path

# Database Connection Settings
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/devassist")

def get_db_connection():
    """Returns a new connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise e

# Backend API Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
