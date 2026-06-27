import os
import cv2
import numpy as np
import csv
from datetime import datetime

filename = "attendance.csv"

# Ensure header exists
if not os.path.exists(filename) or os.path.getsize(filename) == 0:
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Date", "Time", "Status"])

def mark_attendance(name, filename="attendance.csv"):
    today = datetime.now().strftime("%d-%m-%Y")
    now_time = datetime.now().strftime("%H:%M:%S")
    already_present = False

    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] == name and row["Date"] == today and row["Status"] == "Present":
                already_present = True
                break

    if already_present:
        return "already"
    else:
        with open(filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name, today, now_time, "Present"])
        return "recorded"

# Face recognition setup
data_path = "data"
faces, labels, names = [], [], []
label_id = 0
for person in os.listdir(data_path):
    person_path = os.path.join(data_path, person)
    if not os.path.isdir(person_path):
        continue
    names.append(person)
    for img_file in os.listdir(person_path):
        img_path = os.path.join(person_path, img_file)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        faces.append(img)
        labels.append(label_id)
    label_id += 1

if not faces:
    print("[Error] No training data found! Please register users first.")
    exit()

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, np.array(labels))

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

print("[Camera] Starting automatic attendance system (no need to press 'Q').")

recorded_today=set()

while True:
    ret, frame = cap.read()
    if not ret: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces_detected:
        face = gray[y:y+h, x:x+w]
        label, confidence = recognizer.predict(face)
        name = names[label] if confidence < 70 else "Unknown"

        if name != "Unknown":
            if name not in recorded_today:
                # Return value from mark_attendance!
                attendance_marked = mark_attendance(name)
                if attendance_marked == "already":
                    print(f"{name}: Already Recorded Today")
                else:
                    print(f"{name}: Attendance Recorded")
                recorded_today.add(name)
            # Display overlays
            cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

    cv2.imshow("Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # If you want to exit, close the camera window manually, or use Ctrl+C in terminal

    # Remove the waitKey 'Q' check to make it fully automatic

# When done (e.g., you close camera), release resources
cap.release()
cv2.destroyAllWindows()