import sys
import os
import socket
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def check_port(host, port):
    """Returns True if the port is open and listening."""
    try:
        with socket.create_connection((host, port), timeout=1.0) as sock:
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def run_health_check():
    print("=========================================")
    print("        SYSTEM HEALTH DIAGNOSTIC         ")
    print("=========================================\n")
    
    # 1. Check PostgreSQL
    db_port = 5432
    db_status = check_port("localhost", db_port)
    print(f"PostgreSQL Port ({db_port:04}) : {'[ ONLINE ]' if db_status else '[ OFFLINE ]'}")
    
    # 2. Check Redis
    redis_port = 6379
    redis_status = check_port("localhost", redis_port)
    print(f"Redis Port ({redis_port:04})      : {'[ ONLINE ]' if redis_status else '[ OFFLINE ]'}")
    
    # 3. Check Express Backend Server
    backend_port = 5000
    backend_status = check_port("localhost", backend_port)
    print(f"Express Backend ({backend_port:04}) : {'[ ONLINE ]' if backend_status else '[ OFFLINE ]'}")
    
    # 4. Check Vite Frontend Server
    frontend_port = 3000
    frontend_status = check_port("localhost", frontend_port)
    print(f"Vite Frontend ({frontend_port:04})   : {'[ ONLINE ]' if frontend_status else '[ OFFLINE ]'}")
    
    # 5. DB Connectivity Test
    print("\n-----------------------------------------")
    print("Testing DB Connection & Schema...")
    try:
        conn = app_config.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [row[0] for row in cursor.fetchall()]
        print("  Database Link     : OK")
        print(f"  Existing Tables   : {tables}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"  Database Link     : FAILED - {e}")
        
    # 6. Backend API Connectivity Test
    print("\nTesting Backend API REST Health...")
    try:
        res = requests.get(f"{app_config.BACKEND_URL}/api/logs")
        if res.status_code == 200:
            print("  REST Endpoint     : OK")
        else:
            print(f"  REST Endpoint     : HTTP ERROR - Status {res.status_code}")
    except Exception as e:
        print(f"  REST Endpoint     : API LINK OFFLINE - {e}")
        
    print("\n=========================================")

if __name__ == "__main__":
    run_health_check()
