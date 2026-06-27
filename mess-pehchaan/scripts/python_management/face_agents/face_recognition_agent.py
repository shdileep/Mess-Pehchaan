import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config
from deepface import DeepFace

def cosine_distance(v1, v2):
    """Computes cosine distance between two vectors."""
    a = np.array(v1)
    b = np.array(v2)
    return 1 - (np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def recognize_user(image_path, distance_threshold=0.4):
    if not os.path.exists(image_path):
        print(f"Error: Image path not found: {image_path}")
        return None
        
    print(f"AI Face Recognition Agent initiating for {image_path}...")
    
    # 1. Extract embedding using expression-invariant model Facenet and detector RetinaFace
    try:
        representations = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet",
            detector_backend="opencv",
            enforce_detection=True
        )
    except Exception as e:
        print(f"AI Agent: Error detecting face or extracting representation: {e}")
        return None
        
    if not representations:
        print("AI Agent: No faces found in the input image.")
        return None
        
    input_embedding = representations[0]["embedding"]
    print("AI Agent: Target face embedding computed successfully.")
    
    # 2. Retrieve registered users from PostgreSQL
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name, reg_no, face_embedding FROM mess_users")
        registered_users = cursor.fetchall()
        
        if not registered_users:
            print("AI Agent: No users registered in the database. Please register users first.")
            return None
            
        print(f"AI Agent: Comparing input with {len(registered_users)} registered users...")
        best_match = None
        min_distance = 999.0
        
        # 3. Perform Vector Distance Search (Expression-Invariant Cosine distance)
        for user_id, name, reg_no, face_embedding in registered_users:
            # PostgreSQL stores face_embedding as a double precision array
            # face-api.js embeddings are 128-dimensional. If the stored embedding size doesn't match
            # our extracted embedding size, we might need to handle scaling or use Facenet 128.
            # DeepFace Facenet outputs 128 dimensions by default.
            if len(face_embedding) != len(input_embedding):
                # Handle dimension mismatch safely
                continue
                
            dist = cosine_distance(input_embedding, face_embedding)
            
            # Since deep learning embeddings are expression-invariant, 
            # cosine distance will remain low (< 0.4) even with smile, anger, or frowning.
            if dist < min_distance:
                min_distance = dist
                best_match = {
                    "id": user_id,
                    "name": name,
                    "reg_no": reg_no,
                    "distance": dist
                }
                
        # 4. Evaluate Threshold matching
        if best_match and min_distance <= distance_threshold:
            print("\n=========================================")
            print("         AI MATCH IDENTIFIED!            ")
            print("=========================================")
            print(f"Name      : {best_match['name']}")
            print(f"Reg No    : {best_match['reg_no']}")
            print(f"Distance  : {min_distance:.4f} (Threshold: {distance_threshold})")
            print("=========================================")
            
            # 5. Log attendance automatically
            cursor.execute(
                "INSERT INTO mess_attendance_logs (user_id, meal_type) VALUES (%s, %s)",
                (best_match["id"], "AI_RECOG")
            )
            conn.commit()
            print("Attendance recorded under AI_RECOG slot.")
            return best_match
        else:
            print("\n=========================================")
            print("         AI MATCH NOT IDENTIFIED         ")
            print("=========================================")
            if best_match:
                print(f"Closest: {best_match['name']} ({best_match['reg_no']}) with Distance: {min_distance:.4f}")
            print("Verdict: Face not recognized in system database.")
            print("=========================================")
            return None
            
    except Exception as e:
        print(f"AI Agent DB Error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python face_recognition_agent.py <image_path> [threshold]")
        sys.exit(1)
        
    img_path = sys.argv[1]
    thresh = float(sys.argv[2]) if len(sys.argv) > 2 else 0.4
    recognize_user(img_path, thresh)
