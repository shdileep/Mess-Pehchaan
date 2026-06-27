import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

def generate_visualizations(output_image="attendance_analysis.png"):
    print("Generating attendance visualization charts...")
    conn = app_config.get_db_connection()
    
    try:
        # Load logs into pandas DataFrame
        query = """
            SELECT al.marked_at, al.meal_type, u.name
            FROM mess_attendance_logs al
            JOIN mess_users u ON al.user_id = u.id
        """
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No attendance data found in database. Seed mock data first!")
            return
            
        df['marked_at'] = pd.to_datetime(df['marked_at'])
        df['date'] = df['marked_at'].dt.date
        
        # Setup subplot figure
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # 1. Meal Type Distribution Chart
        meal_counts = df['meal_type'].value_counts()
        meal_counts.plot(
            kind='bar', 
            ax=axes[0], 
            color=['skyblue', 'orange', 'lightgreen', 'salmon'],
            edgecolor='black'
        )
        axes[0].set_title("Meal Scans Distribution", fontsize=14, fontweight='bold')
        axes[0].set_xlabel("Meal Type", fontsize=12)
        axes[0].set_ylabel("Scan Count", fontsize=12)
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].grid(axis='y', linestyle='--', alpha=0.7)
        
        # 2. Daily Scans Trend Chart
        daily_counts = df.groupby('date').size()
        daily_counts.plot(
            kind='line', 
            ax=axes[1], 
            marker='o', 
            color='darkviolet', 
            linewidth=2
        )
        axes[1].set_title("Daily Scan Activity Trend", fontsize=14, fontweight='bold')
        axes[1].set_xlabel("Date", fontsize=12)
        axes[1].set_ylabel("Total Scans", fontsize=12)
        axes[1].grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(output_image, dpi=150)
        plt.close()
        
        print(f"Visualization graphs saved successfully to {os.path.abspath(output_image)}")
        
    except Exception as e:
        print(f"Error generating charts: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "attendance_analysis.png"
    generate_visualizations(out)
