import sys
import os
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def export_logs_csv(output_file="attendance_logs.csv"):
    print(f"Exporting attendance logs to {output_file}...")
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT al.id, u.name, u.reg_no, al.meal_type, al.marked_at
            FROM mess_attendance_logs al
            JOIN mess_users u ON al.user_id = u.id
            ORDER BY al.marked_at DESC
        """)
        
        rows = cursor.fetchall()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Log ID", "Name", "Reg No", "Meal Type", "Marked At"])
            writer.writerows(rows)
            
        print(f"Successfully exported {len(rows)} records to {os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"Error exporting logs: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "attendance_logs.csv"
    export_logs_csv(out)
