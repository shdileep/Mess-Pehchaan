import sys
import os
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config
from retinaface import RetinaFace

def detect_and_save_faces(image_path, output_dir="detected_crops"):
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return
        
    print(f"Processing image {image_path} with RetinaFace detector...")
    try:
        # Detect faces
        resp = RetinaFace.detect_faces(image_path)
        
        if not resp or not isinstance(resp, dict):
            print("No faces detected in the image.")
            return
            
        print(f"Detected {len(resp)} face(s). Saving crops...")
        os.makedirs(output_dir, exist_ok=True)
        img = Image.open(image_path)
        
        saved_files = []
        for key, face_data in resp.items():
            facial_area = face_data["facial_area"] # [x1, y1, x2, y2]
            crop = img.crop((facial_area[0], facial_area[1], facial_area[2], facial_area[3]))
            
            crop_path = os.path.join(output_dir, f"crop_{key}_{os.path.basename(image_path)}")
            crop.save(crop_path)
            saved_files.append(crop_path)
            print(f"  Saved face crop: {crop_path}")
            
        return saved_files
        
    except Exception as e:
        print(f"Error during face detection: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detect_faces.py <image_path> [output_dir]")
        sys.exit(1)
        
    img_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "detected_crops"
    detect_and_save_faces(img_path, out_dir)
