
from datetime import datetime

try:
    from .database import get_connection
except ImportError:
    from database import get_connection


def save_event(
    event_type,
    object_type,
    track_id=None,
    confidence=None,
    camera_id="camera_1",
    zone_id=None,
    details=None
):
    """Save one surveillance event to the database."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO surveillance_events (
            event_type,
            object_type,
            track_id,
            confidence,
            camera_id,
            zone_id,
            event_time,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_type,
            object_type,
            track_id,
            confidence,
            camera_id,
            zone_id,
            datetime.now().astimezone().isoformat(timespec="seconds"),
            details
        )
    )

    connection.commit()
    connection.close()


def get_recent_events(limit=10):
    """Retrieve the most recent surveillance events."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT event_id, event_type, object_type, track_id,
               confidence, camera_id, zone_id, event_time, details
        FROM surveillance_events
        ORDER BY event_id DESC
        LIMIT ?
        """,
        (limit,)
    )

    events = [dict(row) for row in cursor.fetchall()]
    connection.close()

    return events

def get_event_counts():
    """Count recorded events by object type."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT object_type, COUNT(*) AS total
        FROM surveillance_events
        GROUP BY object_type
        ORDER BY total DESC
        """
    )

    counts = [dict(row) for row in cursor.fetchall()]
    connection.close()

    return counts



def answer_surveillance_query(question):
    """Answer basic natural-language questions using database records."""

    question = question.lower().strip()

    if "how many" in question or "count" in question:
        counts = get_event_counts()

        if not counts:
            return "No surveillance events have been recorded yet."

        lines = []
        for item in counts:
            object_type = item["object_type"]
            total = item["total"]
            label = "detection" if total == 1 else "detections"
            lines.append(f"{object_type.title()}: {total} {label}")

        return "\n".join(lines)

    if "recent" in question or "latest" in question:
        events = get_recent_events()

        if not events:
            return "No recent surveillance events found."

        lines = []
        for event in events:
            lines.append(
                f'{event["event_time"]} - '
                f'{event["object_type"].title()} detected '
                f'(Track ID: {event["track_id"]})'
            )

        return "\n".join(lines)

    return (
        "I don't understand that question yet. "
        "Try asking about detection counts or recent events."
    )
