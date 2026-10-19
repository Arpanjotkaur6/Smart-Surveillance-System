
import cv2
from ultralytics import YOLO

# Load the YOLO model
model = YOLO("yolo11n.pt")

# Open the webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera.")
    exit()

print("YOLO object detection started.")
print("Press 'q' to quit.")

while True:
    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read frame.")
        break

    # Detect objects in the current frame
    results = model(frame, verbose=False)

    # Draw detection boxes and labels
    annotated_frame = results[0].plot()

    cv2.imshow("Smart Surveillance - Object Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
