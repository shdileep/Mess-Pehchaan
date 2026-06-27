import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def export_logs_excel(output_file="attendance_logs.xlsx"):
    print(f"Exporting attendance logs to {output_file}...")
    conn = app_config.get_db_connection()
    
    try:
        query = """
            SELECT al.id as "Log ID", u.name as "Name", u.reg_no as "Reg No", 
                   al.meal_type as "Meal Type", al.marked_at as "Marked At"
            FROM mess_attendance_logs al
            JOIN mess_users u ON al.user_id = u.id
            ORDER BY al.marked_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        # Save to excel
        df.to_excel(output_file, index=False, sheet_name="Attendance Logs")
        
        print(f"Successfully exported {len(df)} records to {os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"Error exporting to Excel: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "attendance_logs.xlsx"
    export_logs_excel(out)
