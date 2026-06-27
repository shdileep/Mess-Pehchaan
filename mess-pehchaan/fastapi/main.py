import sys
import os
import base64
import numpy as np
import cv2
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Add the python_management folder to sys.path to import app_config
SYS_PATH_DIR = r"D:\Mess Pehchaan\mess-pehchaan\scripts\python_management"
if SYS_PATH_DIR not in sys.path:
    sys.path.insert(0, SYS_PATH_DIR)

import app_config
from deepface import DeepFace

# Set legacy Keras backend to avoid loading issues in tensorflow 2.16+
os.environ["TF_USE_LEGACY_KERAS"] = "1"

app = FastAPI(title="Mess Pehchaan AI Face Recognition API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class RegisterBase64Request(BaseModel):
    name: str
    reg_no: str
    images: List[str]  # List of base64 images

class RecognizeBase64Request(BaseModel):
    image: str  # base64 image

def decode_base64_image(base64_str: str) -> np.ndarray:
    """Decodes a base64 image string into a OpenCV image (NumPy array)."""
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        img_bytes = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image bytes.")
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")

def get_meal_greeting(name: str):
    """Determines the current meal slot and generates a greeting."""
    now = datetime.now()
    hours = now.hour
    minutes = now.minute
    time_val = hours * 60 + minutes

    breakfast_start = 6 * 60
    breakfast_end = 11 * 60 + 30

    lunch_start = 12 * 60
    lunch_end = 15 * 60

    snacks_start = 16 * 60
    snacks_end = 19 * 60

    dinner_start = 19 * 60 + 30
    dinner_end = 22 * 60

    meal_type = 'Closed'
    greeting = f"Hello, {name}! The mess is currently closed, but nice seeing you!"

    if breakfast_start <= time_val <= breakfast_end:
        meal_type = 'Breakfast'
        greeting = f"Good morning, {name}! Hope you have a great breakfast!"
    elif lunch_start <= time_val <= lunch_end:
        meal_type = 'Lunch'
        greeting = f"Hope you enjoy your hearty lunch, {name}!"
    elif snacks_start <= time_val <= snacks_end:
        meal_type = 'Snacks'
        greeting = f"Time for a quick tea break, {name}!"
    elif dinner_start <= time_val <= dinner_end:
        meal_type = 'Dinner'
        greeting = f"Good evening, {name}! Have a pleasant dinner!"

    return meal_type, greeting

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/register")
def register_user(req: RegisterBase64Request):
    """Registers a user by extracting face embeddings from multiple base64 images."""
    if not req.name or not req.reg_no or not req.images:
        raise HTTPException(status_code=400, detail="Name, registration number, and images are required.")

    # Process and average embeddings
    embeddings = []
    for idx, img_b64 in enumerate(req.images):
        try:
            img = decode_base64_image(img_b64)
            representations = DeepFace.represent(
                img_path=img,
                model_name="Facenet",
                detector_backend="opencv",
                enforce_detection=True
            )
            if representations:
                embeddings.append(representations[0]["embedding"])
        except Exception as e:
            print(f"Error processing image {idx}: {e}")

    if not embeddings:
        raise HTTPException(status_code=400, detail="Failed to detect face or extract embedding from any provided images.")

    # Calculate average embedding
    avg_embedding = np.mean(embeddings, axis=0).tolist()

    # Save to PostgreSQL
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO mess_users (name, reg_no, face_embedding) VALUES (%s, %s, %s) RETURNING id, name, reg_no",
            (req.name.strip(), req.reg_no.strip().upper(), avg_embedding)
        )
        user = cursor.fetchone()
        conn.commit()
        return {"success": True, "user": {"id": user[0], "name": user[1], "reg_no": user[2]}}
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "23505" in str(e):
            raise HTTPException(status_code=400, detail=f"Registration number {req.reg_no} is already registered.")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.post("/api/recognize")
def recognize_user(req: RecognizeBase64Request, distance_threshold: float = 0.4):
    """Recognizes a user from a base64 image using Facenet embeddings and Cosine Similarity."""
    if not req.image:
        raise HTTPException(status_code=400, detail="Image base64 data is required.")

    try:
        img = decode_base64_image(req.image)
        representations = DeepFace.represent(
            img_path=img,
            model_name="Facenet",
            detector_backend="opencv",
            enforce_detection=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Face detection or representation failed: {str(e)}")

    if not representations:
        raise HTTPException(status_code=400, detail="No faces detected in the image.")

    captured_emb = np.array(representations[0]["embedding"])

    # Load all registered users from DB
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, reg_no, face_embedding FROM mess_users")
        rows = cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    best_match_user = None
    min_distance = float("inf")

    for uid, name, reg_no, db_emb_list in rows:
        if not db_emb_list:
            continue
        # Compute Cosine distance
        db_emb = np.array(db_emb_list)
        dot_product = np.dot(captured_emb, db_emb)
        norm_a = np.linalg.norm(captured_emb)
        norm_b = np.linalg.norm(db_emb)
        cosine_distance = 1.0 - (dot_product / (norm_a * norm_b))

        if cosine_distance < min_distance:
            min_distance = cosine_distance
            best_match_user = {"id": uid, "name": name, "reg_no": reg_no}

    if min_distance <= distance_threshold and best_match_user:
        meal_type, greeting = get_meal_greeting(best_match_user["name"])

        # Insert log into database
        conn = app_config.get_db_connection()
        cursor = conn.cursor()
        try:
            # Check rate limiting: prevent marking attendance twice in 30 seconds
            cursor.execute(
                "SELECT marked_at FROM mess_attendance_logs WHERE user_id = %s ORDER BY marked_at DESC LIMIT 1",
                (best_match_user["id"],)
            )
            last_log = cursor.fetchone()
            
            if last_log:
                time_diff = (datetime.now() - last_log[0].replace(tzinfo=None)).total_seconds()
                if time_diff < 30:
                    return {
                        "match": True,
                        "name": best_match_user["name"],
                        "reg_no": best_match_user["reg_no"],
                        "meal_type": meal_type,
                        "greeting": greeting,
                        "rate_limited": True,
                        "message": "Attendance already recorded recently (30s cooldown)."
                    }

            if meal_type != 'Closed':
                cursor.execute(
                    "INSERT INTO mess_attendance_logs (user_id, meal_type) VALUES (%s, %s)",
                    (best_match_user["id"], meal_type)
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error logging attendance: {e}")
        finally:
            cursor.close()
            conn.close()

        return {
            "match": True,
            "name": best_match_user["name"],
            "reg_no": best_match_user["reg_no"],
            "meal_type": meal_type,
            "greeting": greeting,
            "rate_limited": False,
            "message": "Attendance recorded successfully!"
        }

    return {"match": False, "message": "Face not recognized."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
