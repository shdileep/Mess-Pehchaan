import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def restore_database(backup_file="database_backup.json"):
    if not os.path.exists(backup_file):
        print(f"Backup file not found at: {backup_file}")
        return
        
    print(f"Restoring database from {os.path.abspath(backup_file)}...")
    with open(backup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data first
        cursor.execute("TRUNCATE TABLE mess_attendance_logs RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE mess_users RESTART IDENTITY CASCADE")
        
        users_inserted = 0
        logs_inserted = 0
        
        # Insert users and map old ID to new ID
        id_map = {}
        for u in data.get("users", []):
            cursor.execute(
                "INSERT INTO mess_users (name, reg_no, face_embedding, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
                (u["name"], u["reg_no"], u["face_embedding"], u["created_at"])
            )
            new_id = cursor.fetchone()[0]
            id_map[u["id"]] = new_id
            users_inserted += 1
            
        # Insert logs using mapped user IDs
        for l in data.get("logs", []):
            mapped_user_id = id_map.get(l["user_id"])
            if mapped_user_id:
                cursor.execute(
                    "INSERT INTO mess_attendance_logs (user_id, meal_type, marked_at) VALUES (%s, %s, %s)",
                    (mapped_user_id, l["meal_type"], l["marked_at"])
                )
                logs_inserted += 1
                
        conn.commit()
        print("Database restored successfully!")
        print(f"Restored {users_inserted} users and {logs_inserted} attendance logs.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error restoring database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "database_backup.json"
    restore_database(inp)
