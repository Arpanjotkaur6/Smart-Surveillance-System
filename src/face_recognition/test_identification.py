
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from face_recognition.face_detector import FaceDetector
from face_recognition.face_recognizer import FaceRecognizer
from face_recognition.identify_person import identify_person


def main():

    detector = FaceDetector()
    recognizer = FaceRecognizer()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    print("Face identification started. Press 'q' to exit.")

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

                    embedding = recognizer.get_embedding(
                        frame, face
                    )

                    name, similarity = identify_person(embedding)
                    print(f"Name: {name} | Similarity: {similarity:.4f}")

                    if name == "Unknown":
                        color = (0, 0, 255)
                    else:
                        color = (0, 255, 0)

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + width, y + height),
                        color,
                        2
                    )

                    label = f"{name} ({similarity:.2f})"

                    cv2.putText(
                        frame,
                        label,
                        (x, max(y - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2
                    )

            cv2.imshow("Known and Unknown Person Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
