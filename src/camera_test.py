print("Smart Surveillance System")
print("Camera module starting...")

import cv2
from datetime import datetime

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera.")
    exit()

# Get camera resolution
width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Create a unique filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
video_path = f"recordings/surveillance_{timestamp}.mp4"

# Create video writer
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))

print("Camera opened successfully.")
print("Recording:", video_path)

while True:
    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read frame.")
        break

    writer.write(frame)

    cv2.imshow("Smart Surveillance - Recording", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
writer.release()
cv2.destroyAllWindows()

print("Recording saved successfully.")