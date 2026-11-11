
from datetime import datetime
import numpy as np

from database.database import get_connection


def save_authorized_person(person_name, face_embedding):
    """Save an authorized person's name and face embedding."""

    if not person_name or not person_name.strip():
        raise ValueError("Person name cannot be empty.")

    embedding = np.asarray(face_embedding, dtype=np.float32)

    if embedding.size != 128:
        raise ValueError("Face embedding must contain 128 values.")

    embedding_bytes = embedding.tobytes()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO authorized_persons
            (person_name, face_embedding, created_at)
            VALUES (?, ?, ?)
            """,
            (
                person_name.strip(),
                embedding_bytes,
                datetime.now().astimezone().isoformat(timespec="seconds")
            )
        )

        connection.commit()
        print(f"Authorized person saved: {person_name}")

    finally:
        connection.close()
