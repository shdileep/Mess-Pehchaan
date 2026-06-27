import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config
from deepface import DeepFace

def register_user_with_expressions(name, reg_no, image_paths):
    if not image_paths:
        print("Error: No images provided for registration.")
        return False
        
    print(f"Registering student: {name} ({reg_no}) under multiple expressions...")
    embeddings = []
    
    for idx, path in enumerate(image_paths, 1):
        if not os.path.exists(path):
            print(f"  Skipping missing image: {path}")
            continue
            
        print(f"  Processing expression image {idx}/{len(image_paths)}: {path}")
        try:
            representations = DeepFace.represent(
                img_path=path,
                model_name="Facenet",
                detector_backend="opencv",
                enforce_detection=True
            )
            if representations:
                embeddings.append(representations[0]["embedding"])
                print(f"    Embedding extracted successfully.")
            else:
                print(f"    No face found in {path}.")
        except Exception as e:
            print(f"    Error processing {path}: {e}")
            
    if not embeddings:
        print("Error: Failed to extract embeddings from any of the provided images.")
        return False
        
    # Calculate expression-invariant average embedding
    average_embedding = np.mean(embeddings, axis=0)
    # Normalize average embedding to unit length (L2 normalization)
    norm = np.linalg.norm(average_embedding)
    final_embedding = (average_embedding / norm).tolist()
    
    print(f"\nAI Agent: Computed robust average embedding vector from {len(embeddings)} expression images.")
    
    # Save to PostgreSQL
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if already registered
        cursor.execute("SELECT id FROM mess_users WHERE reg_no = %s", (reg_no.upper(),))
        existing = cursor.fetchone()
        
        if existing:
            print(f"AI Agent: Registration number {reg_no} is already registered. Updating embedding...")
            cursor.execute(
                "UPDATE mess_users SET name = %s, face_embedding = %s WHERE reg_no = %s",
                (name, final_embedding, reg_no.upper())
            )
        else:
            print(f"AI Agent: Inserting new user record for {name} ({reg_no})...")
            cursor.execute(
                "INSERT INTO mess_users (name, reg_no, face_embedding) VALUES (%s, %s, %s)",
                (name, reg_no.upper(), final_embedding)
            )
            
        conn.commit()
        print("AI Agent: Face registration completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"AI Agent DB Insertion Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python register_face_agent.py <name> <reg_no> <image_path_1> [image_path_2] ...")
        sys.exit(1)
        
    student_name = sys.argv[1]
    student_reg = sys.argv[2]
    imgs = sys.argv[3:]
    register_user_with_expressions(student_name, student_reg, imgs)
