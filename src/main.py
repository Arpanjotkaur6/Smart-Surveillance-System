
import cv2
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO

# Locate the project root and recordings folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECORDINGS_DIR = PROJECT_ROOT / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

# Load the YOLO model
model = YOLO(str(PROJECT_ROOT / "yolo11n.pt"))

# Open the webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera.")
    raise SystemExit(1)

# Read camera properties
width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = camera.get(cv2.CAP_PROP_FPS)

if fps <= 0 or fps > 120:
    fps = 20.0

# Create a unique video filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
video_path = RECORDINGS_DIR / f"surveillance_{timestamp}.mp4"

# Prepare the video writer
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(
    str(video_path),
    fourcc,
    fps,
    (width, height)
)

if not writer.isOpened():
    print("ERROR: Could not create video recording.")
    camera.release()
    raise SystemExit(1)

print("Smart Surveillance System started.")
print(f"Recording to: {video_path}")
print("Press 'q' to stop.")

try:
    while True:
        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read camera frame.")
            break

        # Detect and track objects
        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        # Draw detection boxes, labels, and tracking IDs
        annotated_frame = results[0].plot()

        # Save the annotated surveillance video
        writer.write(annotated_frame)

        # Display the live feed
        cv2.imshow(
            "Smart Surveillance System",
            annotated_frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    writer.release()
    cv2.destroyAllWindows()

print(f"Recording saved: {video_path}")
print("Smart Surveillance System stopped.")
