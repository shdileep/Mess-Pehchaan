import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config
from deepface import DeepFace

def get_face_embedding(image_path, model_name="Facenet", detector_backend="retinaface"):
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return None
        
    print(f"Extracting face embedding using {model_name} (detector: {detector_backend})...")
    try:
        # DeepFace represent returns a list of dictionaries with embedding, facial_area, face, etc.
        embeddings = DeepFace.represent(
            img_path=image_path, 
            model_name=model_name, 
            detector_backend=detector_backend,
            enforce_detection=False
        )
        
        if not embeddings:
            print("No face embeddings extracted.")
            return None
            
        # Get the first face's embedding
        embedding = embeddings[0]["embedding"]
        print(f"Extraction successful. Dimension: {len(embedding)}")
        return embedding
        
    except Exception as e:
        print(f"Error during embedding extraction: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_embedding.py <image_path> [model_name]")
        sys.exit(1)
        
    img_path = sys.argv[1]
    m_name = sys.argv[2] if len(sys.argv) > 2 else "Facenet"
    emb = get_face_embedding(img_path, m_name)
    if emb:
        print(f"Vector preview (first 5 values): {emb[:5]}")
