import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config
from face.extract_embedding import get_face_embedding

def batch_register(images_directory):
    if not os.path.exists(images_directory):
        print(f"Directory not found: {images_directory}")
        return
        
    print(f"Scanning {images_directory} for student face images to register...")
    files = [f for f in os.listdir(images_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not files:
        print("No images found in directory.")
        return
        
    registered_count = 0
    
    for filename in files:
        # Expected format: Firstname_Lastname_RegNo.png (e.g. Rahul_Sharma_21BCE0001.png)
        base = os.path.splitext(filename)[0]
        parts = base.split('_')
        
        if len(parts) < 2:
            print(f"Skipping {filename}: Name format should be FirstName_LastName_RegNo or Name_RegNo")
            continue
            
        reg_no = parts[-1].upper()
        name = " ".join(parts[:-1]).title()
        
        file_path = os.path.join(images_directory, filename)
        print(f"\nProcessing {name} ({reg_no})...")
        
        # Extract 128-d Facenet embedding
        embedding = get_face_embedding(file_path, model_name="Facenet")
        
        if not embedding or len(embedding) != 128:
            print(f"Failed to extract valid 128-d embedding for {filename}.")
            continue
            
        # Call backend API
        payload = {
            "name": name,
            "reg_no": reg_no,
            "face_embedding": embedding
        }
        
        try:
            url = f"{app_config.BACKEND_URL}/api/register"
            res = requests.post(url, json=payload)
            
            if res.status_code == 201:
                print(f"Successfully registered: {name} ({reg_no})")
                registered_count += 1
            else:
                err_msg = res.json().get("error", "Unknown error")
                print(f"Failed to register {name}: Status {res.status_code} - {err_msg}")
                
        except Exception as e:
            print(f"Network error calling backend API: {e}")
            
    print(f"\nBatch registration completed. Registered {registered_count} users successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_register_faces.py <images_directory>")
        sys.exit(1)
        
    batch_register(sys.argv[1])
