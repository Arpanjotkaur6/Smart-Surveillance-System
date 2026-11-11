
import numpy as np

from database.database import get_connection


# Initial SFace cosine similarity threshold.
# We will validate and tune this with real camera tests.
SIMILARITY_THRESHOLD = 0.363


def identify_person(face_embedding):
    """
    Compare a detected face embedding with registered people.

    Returns the person's name if a sufficiently close match is found.
    Otherwise, returns 'Unknown'.
    """

    new_embedding = np.asarray(
        face_embedding,
        dtype=np.float32
    ).reshape(-1)

    if new_embedding.size != 128:
        raise ValueError("Face embedding must contain 128 values.")

    new_norm = np.linalg.norm(new_embedding)

    if new_norm == 0:
        raise ValueError("Invalid face embedding.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT person_name, face_embedding
            FROM authorized_persons
        """)

        registered_people = cursor.fetchall()

    finally:
        connection.close()

    if not registered_people:
        return "Unknown", 0.0

    best_name = "Unknown"
    best_similarity = -1.0

    for person in registered_people:

        stored_embedding = np.frombuffer(
            person["face_embedding"],
            dtype=np.float32
        )

        if stored_embedding.size != 128:
            continue

        stored_norm = np.linalg.norm(stored_embedding)

        if stored_norm == 0:
            continue

        similarity = float(
            np.dot(new_embedding, stored_embedding)
            / (new_norm * stored_norm)
        )

        if similarity > best_similarity:
            best_similarity = similarity
            best_name = person["person_name"]

    if best_similarity >= SIMILARITY_THRESHOLD:
        return best_name, best_similarity

    return "Unknown", best_similarity
