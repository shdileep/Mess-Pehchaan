import cv2
import os

def register_user(username):
    user_path = os.path.join("data", username)
    os.makedirs(user_path, exist_ok=True)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    count = 0
    print("Capturing images... Press 'Q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            face = frame[y:y+h, x:x+w]
            cv2.imwrite(f"{user_path}/{count}.jpg", face)
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        cv2.imshow("Register Face", frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or count >= 50:
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"[OK] Captured {count} images for {username}")

if __name__ == "__main__":
    name = input("Enter your name: ")
    register_user(name)
