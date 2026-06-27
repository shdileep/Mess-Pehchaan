import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def test_logs_api():
    print("Testing /api/logs endpoint...")
    try:
        url = f"{app_config.BACKEND_URL}/api/logs"
        res = requests.get(url)
        
        print(f"Status Code: {res.status_code}")
        print("Response Body (first 3 records):")
        data = res.json()
        print(data[:3])
        
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_logs_api()
