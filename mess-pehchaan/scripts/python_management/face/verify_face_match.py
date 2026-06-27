import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config
from deepface import DeepFace

def verify_faces(img1_path, img2_path, model_name="Facenet", detector_backend="retinaface"):
    if not os.path.exists(img1_path) or not os.path.exists(img2_path):
        print("Error: One or both image paths do not exist.")
        return
        
    print(f"Comparing {img1_path} and {img2_path}...")
    try:
        result = DeepFace.verify(
            img1_path=img1_path,
            img2_path=img2_path,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=False
        )
        
        distance = result["distance"]
        threshold = result["threshold"]
        is_verified = result["verified"]
        
        print("\nVerification Results:")
        print("---------------------")
        print(f"Verified Match : {is_verified}")
        print(f"Cosine Distance: {distance:.4f} (Threshold: {threshold:.4f})")
        print(f"Model Used     : {model_name}")
        print(f"Detector Used  : {detector_backend}")
        
        return is_verified
        
    except Exception as e:
        print(f"Error comparing faces: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_face_match.py <image1_path> <image2_path>")
        sys.exit(1)
        
    verify_faces(sys.argv[1], sys.argv[2])
