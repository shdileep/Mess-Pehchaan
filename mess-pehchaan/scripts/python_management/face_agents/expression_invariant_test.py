import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config
from deepface import DeepFace
from face_agents.face_recognition_agent import cosine_distance

def test_expression_invariance(reg_no, test_image_path, threshold=0.4):
    if not os.path.exists(test_image_path):
        print(f"Error: Test image not found at: {test_image_path}")
        return
        
    print(f"Initiating AI Expression Invariance Diagnostic...")
    print(f"Test Target (Reg No)   : {reg_no.upper()}")
    print(f"New Expression Image   : {test_image_path}")
    
    # 1. Fetch registered embedding
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name, face_embedding FROM mess_users WHERE reg_no = %s", (reg_no.upper(),))
        row = cursor.fetchone()
        
        if not row:
            print(f"Error: No registered user found with Reg No: {reg_no}")
            return
            
        name, registered_embedding = row
        print(f"Registered User Name   : {name}")
        
        # 2. Extract embedding from new expression image
        print("Extracting embedding from new expression image using OpenCV...")
        representations = DeepFace.represent(
            img_path=test_image_path,
            model_name="Facenet",
            detector_backend="opencv",
            enforce_detection=True
        )
        
        if not representations:
            print("Error: Could not detect face in test image.")
            return
            
        test_embedding = representations[0]["embedding"]
        
        # 3. Compute Distance
        distance = cosine_distance(registered_embedding, test_embedding)
        
        print("\n=========================================")
        print("    EXPRESSION INVARIANCE TEST RESULTS   ")
        print("=========================================")
        print(f"Target Student     : {name} ({reg_no.upper()})")
        print(f"Vector Distance    : {distance:.4f}")
        print(f"Cosine Threshold   : {threshold}")
        
        is_match = distance <= threshold
        print(f"Verdict            : {'[ PASS ] - Robust Match Found' if is_match else '[ FAIL ] - Match Mismatch'}")
        print("=========================================")
        
        if is_match:
            print("Success: Face embeddings correctly matched despite facial expression variations.")
        else:
            print("Warning: Facial expression variations exceeded the threshold limits.")
            
    except Exception as e:
        print(f"Diagnostic Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python expression_invariant_test.py <reg_no> <new_expression_image_path> [threshold]")
        sys.exit(1)
        
    reg = sys.argv[1]
    img = sys.argv[2]
    thresh = float(sys.argv[3]) if len(sys.argv) > 3 else 0.4
    test_expression_invariance(reg, img, thresh)
