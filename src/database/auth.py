
import hashlib
import hmac
import secrets
from datetime import datetime

from .database import get_connection


def hash_password(password, salt=None):
    """Create a secure password hash."""

    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        600_000
    )

    return password_hash.hex(), salt


def create_admin(username, password):
    """Create the administrator account."""

    username = username.strip()

    if not username or not password:
        raise ValueError("Username and password cannot be empty.")

    password_hash, salt = hash_password(password)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO administrators
            (username, password_hash, password_salt, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                password_hash,
                salt,
                datetime.now().astimezone().isoformat(timespec="seconds")
            )
        )

        connection.commit()
        print("Administrator account created successfully!")

    finally:
        connection.close()


def verify_admin(username, password):
    """Verify administrator login credentials."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT password_hash, password_salt
            FROM administrators
            WHERE username = ?
            """,
            (username.strip(),)
        )

        admin = cursor.fetchone()

        if admin is None:
            return False

        stored_hash = admin["password_hash"]
        salt = admin["password_salt"]

        calculated_hash, _ = hash_password(password, salt)

        return hmac.compare_digest(stored_hash, calculated_hash)

    finally:
        connection.close()
