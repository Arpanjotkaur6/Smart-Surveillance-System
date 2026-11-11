
import sys
import getpass
from pathlib import Path

import cv2

# Add the project's src folder to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database.auth import verify_admin
from face_recognition.face_detector import FaceDetector
from face_recognition.face_recognizer import FaceRecognizer
from face_recognition.person_manager import save_authorized_person


def main():

    print("===== ADMIN LOGIN =====")

    username = input("Admin username: ")
    password = getpass.getpass("Admin password: ")

    if not verify_admin(username, password):
        print("Access denied! Invalid credentials.")
        return

    print("\nAdmin login successful!")

    person_name = input("Enter the person's name to register: ").strip()

    if not person_name:
        print("Person name cannot be empty.")
        return

    print("\nPlease ensure the person has consented to biometric registration.")

    detector = FaceDetector()
    recognizer = FaceRecognizer()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    print("\nCamera started.")
    print("Position one person's face clearly in the camera.")
    print("Press 's' to register the face.")
    print("Press 'q' to cancel.")

    try:
        while True:

            ret, frame = camera.read()

            if not ret:
                print("Could not read camera frame.")
                break

            faces = detector.detect(frame)

            if faces is not None:

                for face in faces:
                    x, y, width, height = face[:4].astype(int)

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + width, y + height),
                        (0, 255, 0),
                        2
                    )

            cv2.imshow("Authorized Person Registration", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("s"):

                if faces is None or len(faces) != 1:
                    print("Please ensure exactly one face is visible.")
                    continue

                embedding = recognizer.get_embedding(frame, faces[0])

                save_authorized_person(person_name, embedding)

                break

            elif key == ord("q"):
                print("Registration cancelled.")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

