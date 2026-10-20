
from queries import save_event
from database import get_connection


# Insert one sample person-detection event
save_event(
    event_type="detected",
    object_type="person",
    track_id=1,
    confidence=0.95,
    camera_id="camera_1",
    details="Test event"
)

print("Sample event saved successfully!")

# Retrieve the latest saved event
connection = get_connection()
cursor = connection.cursor()

cursor.execute(
    "SELECT * FROM surveillance_events ORDER BY event_id DESC LIMIT 1"
)

event = cursor.fetchone()
connection.close()

print("Latest event:")
print(dict(event) if event else "No event found.")
