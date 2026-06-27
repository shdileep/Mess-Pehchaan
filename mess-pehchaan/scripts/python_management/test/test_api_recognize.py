import sys
import os
import requests
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def test_recognize_api():
    print("Testing /api/recognize endpoint...")
    
    # Generate mock 128-dimensional embedding vector
    embedding = [random.uniform(-1, 1) for _ in range(128)]
    length = sum(x*x for x in embedding) ** 0.5
    embedding = [x / length for x in embedding]
    
    payload = {
        "face_embedding": embedding
    }
    
    try:
        url = f"{app_config.BACKEND_URL}/api/recognize"
        res = requests.post(url, json=payload)
        
        print(f"Status Code: {res.status_code}")
        print("Response Body:")
        print(res.text)
        
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_recognize_api()
