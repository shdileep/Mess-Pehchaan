import sys
import os
import json
from decimal import Decimal
from datetime import datetime

# Import sibling config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

class CustomEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle decimals, datetimes, and float arrays."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(CustomEncoder, self).default(obj)

def backup_database(output_file="backup.json"):
    print("Starting database backup...")
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Fetch users
        cursor.execute("SELECT id, name, reg_no, face_embedding, created_at FROM mess_users")
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "name": row[1],
                "reg_no": row[2],
                "face_embedding": row[3],
                "created_at": row[4]
            })
            
        # Fetch logs
        cursor.execute("SELECT id, user_id, meal_type, marked_at FROM mess_attendance_logs")
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "id": row[0],
                "user_id": row[1],
                "meal_type": row[2],
                "marked_at": row[3]
            })
            
        backup_data = {
            "users": users,
            "logs": logs,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, cls=CustomEncoder, indent=2)
            
        print(f"Database backup written successfully to {os.path.abspath(output_file)}")
        print(f"Backed up {len(users)} users and {len(logs)} attendance logs.")
        
    except Exception as e:
        print(f"Error backing up database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "database_backup.json"
    backup_database(out)
