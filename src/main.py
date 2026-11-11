
import sys
import cv2

from datetime import datetime
from pathlib import Path
from ultralytics import YOLO


# --------------------------------------------------
# PROJECT PATHS AND IMPORTS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from database.queries import save_event
from database.database import get_connection

from face_recognition.face_detector import FaceDetector
from face_recognition.face_recognizer import FaceRecognizer
from face_recognition.identify_person import identify_person


RECORDINGS_DIR = PROJECT_ROOT / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# LOAD MODELS
# --------------------------------------------------

model = YOLO(str(PROJECT_ROOT / "yolo11n.pt"))

face_detector = FaceDetector()
face_recognizer = FaceRecognizer()

print("YOLO model loaded successfully.")
print("Face detection and recognition models loaded successfully.")


# --------------------------------------------------
# OBJECT TRACKING VARIABLES
# --------------------------------------------------
logged_track_ids = set()

person_last_seen = {}


PERSON_EXIT_TIMEOUT_FRAMES = 30

frame_count = 0


# --------------------------------------------------
# FACE TRACKING VARIABLES
# --------------------------------------------------

face_event_last_logged = {}

FACE_EVENT_COOLDOWN_SECONDS = 30

known_person_last_seen = {}
KNOWN_PERSON_EXIT_TIMEOUT_SECONDS = 5

# Unknown-person appearance tracking
unknown_person_last_seen = None
UNKNOWN_PRESENCE_TIMEOUT_SECONDS = 5

known_person_active = set()
known_person_exit_candidate_since = {}
KNOWN_PERSON_EXIT_CONFIRMATION_SECONDS = 2

face_tracks = {}
next_face_track_id = 1

FACE_MATCH_THRESHOLD = 0.3
FACE_TRACK_TIMEOUT_SECONDS = 3


# --------------------------------------------------
# ANIMAL CLASSES
# --------------------------------------------------

ANIMAL_CLASSES = {
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
}


# --------------------------------------------------
# FACE TRACKING HELPER FUNCTION
# --------------------------------------------------

def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union between
    two face bounding boxes.
    """

    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])

    x2 = min(
        box1[0] + box1[2],
        box2[0] + box2[2]
    )

    y2 = min(
        box1[1] + box1[3],
        box2[1] + box2[3]
    )

    intersection = (
        max(0, x2 - x1) *
        max(0, y2 - y1)
    )

    area1 = box1[2] * box1[3]
    area2 = box2[2] * box2[3]

    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return intersection / union


# --------------------------------------------------
# OPEN WEBCAM
# --------------------------------------------------

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera.")
    raise SystemExit(1)


# --------------------------------------------------
# CAMERA SETTINGS
# --------------------------------------------------

width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

fps = camera.get(cv2.CAP_PROP_FPS)

if fps <= 0 or fps > 120:
    fps = 20.0


# --------------------------------------------------
# VIDEO RECORDING SETUP
# --------------------------------------------------

recording_start = datetime.now().astimezone()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

video_path = (
    RECORDINGS_DIR /
    f"surveillance_{timestamp}.mp4"
)

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


# --------------------------------------------------
# MAIN SURVEILLANCE LOOP
# --------------------------------------------------

try:

    while True:

        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read camera frame.")
            break

        frame_count += 1

        # ------------------------------------------
        # YOLO OBJECT DETECTION AND TRACKING
        # ------------------------------------------

        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        current_person_ids = set()

        for box in results[0].boxes:

            class_id = int(box.cls[0])

            object_type = model.names[class_id]

            # Determine object category
            if object_type == "person":
                category = "person"

            elif object_type in ANIMAL_CLASSES:
                category = "animal"

            else:
                category = "other"

            # Get tracking ID
            track_id = (
                int(box.id[0])
                if box.id is not None
                else None
            )

            confidence = float(box.conf[0])

            object_key = track_id

            # --------------------------------------
            # PERSON DETECTION EVENTS
            # --------------------------------------

            if object_type == "person" and track_id is not None:

                current_person_ids.add(track_id)

                last_seen = person_last_seen.get(track_id)

                if (
                    last_seen is None
                    or frame_count - last_seen > PERSON_EXIT_TIMEOUT_FRAMES
                ):

                    save_event(
                        event_type="detected",
                        object_type="person",
                        track_id=track_id,
                        confidence=confidence,
                        camera_id="camera_1",
                        details="Person newly appeared in camera view"
                    )

                    print(
                        f"Person detected: Track ID: {track_id}"
                    )

                person_last_seen[track_id] = frame_count
                

            # --------------------------------------
            # ANIMAL AND OTHER OBJECT EVENTS
            # --------------------------------------

            elif (
                track_id is not None
                and object_key not in logged_track_ids
            ):

                save_event(
                    event_type="detected",
                    object_type=object_type,
                    track_id=track_id,
                    confidence=confidence,
                    camera_id="camera_1",
                    details=(
                        f"Category: {category}; "
                        "First detection of this tracked object"
                    )
                )

                logged_track_ids.add(object_key)

                print(
                    f"Saved event: {object_type}, "
                    f"Track ID: {track_id}"
                )

        visible_person_ids = current_person_ids

        # Create annotated YOLO frame
        annotated_frame = results[0].plot()


        # ------------------------------------------
        # FACE DETECTION
        # ------------------------------------------

        faces = face_detector.detect(frame)

        current_time = datetime.now().timestamp()


        # ------------------------------------------
        # REMOVE EXPIRED FACE TRACKS
        # ------------------------------------------

        expired_tracks = [
            track_id
            for track_id, track_data in face_tracks.items()
            if (
                current_time - track_data["last_seen"]
                > FACE_TRACK_TIMEOUT_SECONDS
            )
        ]

        for track_id in expired_tracks:

            del face_tracks[track_id]

            

        # ------------------------------------------
        # MATCH CURRENT FACES WITH EXISTING TRACKS
        # ------------------------------------------

        matched_face_ids = set()

        if faces is not None:

            for face in faces:

                x, y, face_width, face_height = (
                    face[:4].astype(int)
                )

                current_box = (
                    x,
                    y,
                    face_width,
                    face_height
                )

                best_iou = 0.0
                best_track_id = None

                # Find matching existing face track
                for track_id, track_data in face_tracks.items():

                    if track_id in matched_face_ids:
                        continue

                    previous_box = track_data["box"]

                    iou = calculate_iou(
                        current_box,
                        previous_box
                    )

                    if iou > best_iou:

                        best_iou = iou
                        best_track_id = track_id

                # Assign existing or new face track ID
                if (
                    best_track_id is not None
                    and best_iou >= FACE_MATCH_THRESHOLD
                ):

                    face_track_id = best_track_id

                else:

                    face_track_id = next_face_track_id

                    next_face_track_id += 1

                # Update face track information
                face_tracks[face_track_id] = {
                    "box": current_box,
                    "last_seen": current_time
                }

                matched_face_ids.add(face_track_id)

                print(
                    f"Face Track ID: {face_track_id}"
                )


                # ----------------------------------
                # GENERATE FACE EMBEDDING
                # ----------------------------------

                embedding = face_recognizer.get_embedding(
                    frame,
                    face
                )


                # ----------------------------------
                # IDENTIFY PERSON
                # ----------------------------------

                name, similarity = identify_person(
                    embedding
                )


                # ----------------------------------
                # FACE EVENT LOGGING
                # ----------------------------------

               

                if name == "Unknown":

                    event_type = "unknown_person"
                    details = "Unknown person detected"

                    # Check whether this is a new appearance
                    if (
                        unknown_last_seen is None
                        or current_time - unknown_last_seen
                        > UNKNOWN_PRESENCE_TIMEOUT_SECONDS
                    ):

                        save_event(
                            event_type=event_type,
                            object_type="person",
                            confidence=similarity,
                            details=details
                        )

                        print("New unknown-person appearance logged.")

                    unknown_last_seen = current_time

                else:

                    event_key = name

                    # Log entry only when the person is not currently active
                    if event_key not in known_person_active:

                        save_event(
                            event_type="known_person_entry",
                            object_type="person",
                            confidence=similarity,
                            details=f"{name} entered the camera view"
                        )

                        known_person_active.add(event_key)

                        print(f"Known person entered: {name}")

                    # Refresh last-seen time on every recognition
                    known_person_last_seen[event_key] = current_time
                    known_person_exit_candidate_since.pop(event_key, None)
                                
                # ----------------------------------
                # FACE BOUNDING BOX COLOUR
                # ----------------------------------

                if name == "Unknown":

                    color = (0, 0, 255)

                else:

                    color = (0, 255, 0)


                # ----------------------------------
                # DRAW FACE BOUNDING BOX
                # ----------------------------------

                cv2.rectangle(
                    annotated_frame,
                    (x, y),
                    (x + face_width, y + face_height),
                    color,
                    2
                )


                # ----------------------------------
                # DISPLAY IDENTITY AND SIMILARITY
                # ----------------------------------

                label = (
                    f"{name} ({similarity:.2f})"
                )

                cv2.putText(
                    annotated_frame,
                    label,
                    (x, max(y - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )


        
        # CHECK KNOWN PERSON EXITS

        # CHECK KNOWN PERSON EXITS
        for person_name in list(known_person_active):
            last_seen = known_person_last_seen.get(person_name)

            if last_seen is None:
                continue

            if current_time - last_seen > KNOWN_PERSON_EXIT_TIMEOUT_SECONDS:

                # Start the exit confirmation timer
                if person_name not in known_person_exit_candidate_since:
                    known_person_exit_candidate_since[person_name] = current_time

                # Confirm exit after the additional waiting period
                elif (
                    current_time - known_person_exit_candidate_since[person_name]
                    >= KNOWN_PERSON_EXIT_CONFIRMATION_SECONDS
                ):
                    save_event(
                        event_type="known_person_exit",
                        object_type="person",
                        confidence=0.0,
                        details=f"{person_name} left the camera view"
                    )

                    known_person_active.remove(person_name)
                    known_person_last_seen.pop(person_name, None)
                    known_person_exit_candidate_since.pop(person_name, None)

                    print(f"Known person exited: {person_name}")


        # ------------------------------------------
        # DISPLAY CAMERA WINDOW
        # ------------------------------------------
        writer.write(annotated_frame)
        cv2.imshow("Smart Surveillance System", annotated_frame)


        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Stopping surveillance...")
            break

# --------------------------------------------------
# RELEASE CAMERA AND VIDEO RESOURCES
# --------------------------------------------------

finally:

    camera.release()

    writer.release()

    cv2.destroyAllWindows()


# --------------------------------------------------
# SAVE VIDEO METADATA TO DATABASE
# --------------------------------------------------

recording_end = datetime.now().astimezone()

duration_seconds = (
    recording_end - recording_start
).total_seconds()


connection = get_connection()

try:

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

finally:

    connection.close()


print("Video metadata saved to database.")

print(f"Recording saved: {video_path}")

print("Smart Surveillance System stopped.")
