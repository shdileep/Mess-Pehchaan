import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def clear_database(clear_users=False):
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        if clear_users:
            print("Clearing all registered users and logs...")
            cursor.execute("TRUNCATE TABLE mess_attendance_logs RESTART IDENTITY CASCADE")
            cursor.execute("TRUNCATE TABLE mess_users RESTART IDENTITY CASCADE")
            print("All users and logs deleted.")
        else:
            print("Clearing attendance logs only...")
            cursor.execute("TRUNCATE TABLE mess_attendance_logs RESTART IDENTITY CASCADE")
            print("All attendance logs deleted.")
            
        conn.commit()
        print("Database cleared successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error clearing database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    users_flag = False
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["--all", "-a", "users"]:
        users_flag = True
    clear_database(users_flag)
