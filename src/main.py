import sys

import cv2
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from database.queries import save_event
from database.database import get_connection

# Locate the project root and recordings folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECORDINGS_DIR = PROJECT_ROOT / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

# Load the YOLO model
model = YOLO(str(PROJECT_ROOT / "yolo11n.pt"))
logged_track_ids = set()

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
recording_start = datetime.now().astimezone()
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
        

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            object_type = model.names[class_id]
        
            track_id = (
                int(box.id[0])
                if box.id is not None
                else None
            )
        
            confidence = float(box.conf[0])
        
            if track_id is not None and track_id not in logged_track_ids:
                save_event(
                    event_type="detected",
                    object_type=object_type,
                    track_id=track_id,
                    confidence=confidence,
                    camera_id="camera_1",
                    details="First detection of this tracked object"
                )
        
                logged_track_ids.add(track_id)
                print(f"Saved event: {object_type}, Track ID: {track_id}")
        annotated_frame = results[0].plot()
        writer.write(annotated_frame)
        cv2.imshow("Smart Surveillance System", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    writer.release()
    cv2.destroyAllWindows()

recording_end = datetime.now().astimezone()
duration_seconds = (recording_end - recording_start).total_seconds()


connection = get_connection()
cursor = connection.cursor()

cursor.execute(
    """
    INSERT INTO video_recordings (
        camera_id,
        file_path,
        start_time,
        end_time,
        duration_seconds,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        "camera_1",
        str(video_path.relative_to(PROJECT_ROOT)),
        recording_start.isoformat(timespec="seconds"),
        recording_end.isoformat(timespec="seconds"),
        duration_seconds,
        datetime.now().astimezone().isoformat(timespec="seconds")
    )
)

connection.commit()
connection.close()

print("Video metadata saved to database.")

print(f"Recording saved: {video_path}")
print("Smart Surveillance System stopped.")
