import sys
import os
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app_config

MOCK_USERS = [
    {"name": "Aarav Sharma", "reg_no": "21BCE0001"},
    {"name": "Diya Iyer", "reg_no": "21BDS0054"},
    {"name": "Kabir Verma", "reg_no": "22BEE0112"},
    {"name": "Ananya Nair", "reg_no": "22BIT0042"},
    {"name": "Rohan Gupta", "reg_no": "21BCS0089"},
    {"name": "Meera Sen", "reg_no": "23BCE0231"},
    {"name": "Vikram Reddy", "reg_no": "21BDS0155"},
    {"name": "Pooja Hegde", "reg_no": "22BCE1002"},
    {"name": "Siddharth Rao", "reg_no": "23BIT0811"},
    {"name": "Riya Kapoor", "reg_no": "21BEC0234"}
]

MEALS = ["Breakfast", "Lunch", "Snacks", "Dinner"]

def generate_mock_embedding():
    # face-api.js uses a 128-dimensional embedding vector (normalized to unit length)
    vec = [random.uniform(-1, 1) for _ in range(128)]
    length = sum(x*x for x in vec) ** 0.5
    return [x / length for x in vec]

def seed_database():
    print("Seeding database with mock data...")
    conn = app_config.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing logs & users
        cursor.execute("TRUNCATE TABLE mess_attendance_logs RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE mess_users RESTART IDENTITY CASCADE")
        
        user_ids = []
        # Seed users
        for u in MOCK_USERS:
            emb = generate_mock_embedding()
            cursor.execute(
                "INSERT INTO mess_users (name, reg_no, face_embedding) VALUES (%s, %s, %s) RETURNING id",
                (u["name"], u["reg_no"], emb)
            )
            uid = cursor.fetchone()[0]
            user_ids.append(uid)
            print(f"Seeded User: {u['name']} ({u['reg_no']})")
            
        # Seed logs for the past 7 days
        log_count = 0
        now = datetime.now()
        for day in range(7):
            date_offset = now - timedelta(days=day)
            
            # For each user, randomly mark some meals
            for uid in user_ids:
                for meal in MEALS:
                    # 75% chance of marking attendance
                    if random.random() < 0.75:
                        # Generate random time within meal window
                        if meal == "Breakfast":
                            hour = random.randint(7, 9)
                        elif meal == "Lunch":
                            hour = random.randint(12, 14)
                        elif meal == "Snacks":
                            hour = random.randint(16, 18)
                        else:
                            hour = random.randint(20, 21)
                        
                        minute = random.randint(0, 59)
                        second = random.randint(0, 59)
                        
                        log_time = date_offset.replace(hour=hour, minute=minute, second=second)
                        
                        cursor.execute(
                            "INSERT INTO mess_attendance_logs (user_id, meal_type, marked_at) VALUES (%s, %s, %s)",
                            (uid, meal, log_time)
                        )
                        log_count += 1
                        
        conn.commit()
        print(f"\nDatabase seeded successfully!")
        print(f"Created {len(user_ids)} mock users.")
        print(f"Generated {log_count} historical attendance logs.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_database()
