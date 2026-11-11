
import cv2

from face_detector import FaceDetector
from face_recognizer import FaceRecognizer


def main():

    detector = FaceDetector()
    recognizer = FaceRecognizer()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    print("Face recognition test started. Press 'q' to exit.")

    while True:

        ret, frame = camera.read()

        if not ret:
            print("Could not read camera frame.")
            break

        faces = detector.detect(frame)

        if faces is not None:

            for face in faces:

                x, y, width, height = face[:4].astype(int)

                embedding = recognizer.get_embedding(frame, face)

                print("Face embedding shape:", embedding.shape)

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + width, y + height),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "Face Recognized",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

        cv2.imshow("SFace Recognition Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
