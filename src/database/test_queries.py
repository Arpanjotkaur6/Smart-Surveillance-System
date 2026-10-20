
from queries import (
    save_event,
    get_recent_events,
    get_event_counts,
    answer_surveillance_query
)
from database import get_connection
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))




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



from queries import get_recent_events

print("\nRecent surveillance events:")

for event in get_recent_events(limit=5):
    print(event)


print("\nEvent counts by object type:")

for item in get_event_counts():
    print(f"{item['object_type']}: {item['total']}")

print("\nNLP Query Test 1:")
print(answer_surveillance_query("How many detections are recorded?"))

print("\nNLP Query Test 2:")
print(answer_surveillance_query("Show recent events"))

print("\nNLP Query Test 3:")
print(answer_surveillance_query("What is the weather today?"))    