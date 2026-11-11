
import cv2
from face_detector import FaceDetector


def main():
    detector = FaceDetector()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    print("Face detection started. Press 'q' to exit.")

    while True:
        ret, frame = camera.read()

        if not ret:
            print("Error: Could not read camera frame.")
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

                cv2.putText(
                    frame,
                    "Face Detected",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

        cv2.imshow("YuNet Face Detection Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
