from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database.database import get_connection


connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT event_id, event_type, object_type,
           confidence, event_time, details
    FROM surveillance_events
    WHERE event_type IN (
        'known_person_entry',
        'known_person_exit',
        'unknown_person'
    )
    ORDER BY event_id DESC
    LIMIT 20
""")

events = cursor.fetchall()
connection.close()

print("\nFace Recognition Events:")
print("-" * 60)

if events:
    for event in events:
        print(dict(event))
else:
    print("No face-recognition events found.")