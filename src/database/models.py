
from database import get_connection


def create_tables():
    """Create the tables required for surveillance records."""

    connection = get_connection()
    cursor = connection.cursor()

    # Store person, animal, and other detection events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS surveillance_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            object_type TEXT NOT NULL,
            track_id INTEGER,
            confidence REAL,
            camera_id TEXT DEFAULT 'camera_1',
            zone_id TEXT,
            event_time TEXT NOT NULL,
            details TEXT
        )
    """)

    # Store metadata for each saved surveillance video
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_recordings (
            video_id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_seconds REAL,
            created_at TEXT NOT NULL
        )
    """)

    # Store authorized people and their face embeddings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authorized_persons (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            face_embedding BLOB NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    
    # Store administrator login credentials
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administrators (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
   


    connection.commit()
    connection.close()

    print("Surveillance database tables created successfully!")


if __name__ == "__main__":
    create_tables()
