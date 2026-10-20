
from database.database import get_connection
from datetime import datetime


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
