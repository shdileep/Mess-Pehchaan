import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def print_attendance_stats():
    print("Computing Mess Attendance Statistics...\n")
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM mess_users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM mess_attendance_logs")
        total_logs = cursor.fetchone()[0]
        
        print(f"=========================================")
        print(f"Total Registered Users : {total_users}")
        print(f"Total Attendance Scans  : {total_logs}")
        print(f"=========================================\n")
        
        # Count by Meal Type
        cursor.execute("""
            SELECT meal_type, COUNT(*) 
            FROM mess_attendance_logs 
            GROUP BY meal_type 
            ORDER BY count DESC
        """)
        print("Scans by Meal Type:")
        print("------------------")
        for row in cursor.fetchall():
            print(f"  {row[0]:<12}: {row[1]} scans")
        print()
        
        # Most Active Students
        cursor.execute("""
            SELECT u.name, u.reg_no, COUNT(al.id) as scan_count
            FROM mess_attendance_logs al
            JOIN mess_users u ON al.user_id = u.id
            GROUP BY u.id, u.name, u.reg_no
            ORDER BY scan_count DESC
            LIMIT 5
        """)
        print("Most Active Students:")
        print("---------------------")
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {row[0]} ({row[1]}) - {row[2]} meals marked")
        print()
        
        # Scans by Day
        cursor.execute("""
            SELECT DATE(marked_at) as log_date, COUNT(*) 
            FROM mess_attendance_logs 
            GROUP BY log_date 
            ORDER BY log_date DESC 
            LIMIT 7
        """)
        print("Scans for Past 7 Days:")
        print("----------------------")
        for row in cursor.fetchall():
            print(f"  {row[0]} : {row[1]} scans")
            
    except Exception as e:
        print(f"Error computing stats: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print_attendance_stats()
