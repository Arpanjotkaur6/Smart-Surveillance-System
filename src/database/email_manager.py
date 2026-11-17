
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from .database import get_connection

try:
    from email_service import send_alert_email
except ImportError:
    from src.email_service import send_alert_email

def hash_code(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def generate_code():
    return str(secrets.randbelow(900000) + 100000)


def current_time():
    return datetime.now().astimezone()


# --------------------------------------------------
# EMAIL RECIPIENT VERIFICATION
# --------------------------------------------------

def add_email_recipient(email):
    email = email.strip().lower()

    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Enter a valid email address.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT recipient_id, is_verified FROM admin_email_recipients WHERE email = ?",
            (email,)
        )

        existing = cursor.fetchone()

        if existing and existing["is_verified"]:
            raise ValueError("This email address is already verified.")

        if not existing:
            cursor.execute(
                """
                INSERT INTO admin_email_recipients
                (email, is_verified, is_primary, created_at)
                VALUES (?, 0, 0, ?)
                """,
                (email, current_time().isoformat(timespec="seconds"))
            )

        cursor.execute(
            "DELETE FROM email_verification_codes WHERE email = ?",
            (email,)
        )

        code = generate_code()
        expires = current_time() + timedelta(minutes=10)

        cursor.execute(
            """
            INSERT INTO email_verification_codes
            (email, code_hash, expires_at, attempts, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (
                email,
                hash_code(code),
                expires.isoformat(),
                current_time().isoformat(timespec="seconds")
            )
        )

        connection.commit()

    finally:
        connection.close()

    sent = send_alert_email(
        email,
        "Verify Smart Surveillance Email",
        f"Your verification code is: {code}\n\n"
        "This code expires in 10 minutes."
    )

    if not sent:
        raise RuntimeError("Could not send verification email.")

    return {"message": "Verification code sent successfully."}


def verify_email_recipient(email, code):
    email = email.strip().lower()
    code = code.strip()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT code_id, code_hash, expires_at, attempts
            FROM email_verification_codes
            WHERE email = ?
            ORDER BY code_id DESC
            LIMIT 1
            """,
            (email,)
        )

        record = cursor.fetchone()

        if not record:
            return False

        if record["attempts"] >= 5:
            return False

        if current_time() > datetime.fromisoformat(record["expires_at"]):
            return False

        if not hmac.compare_digest(
            record["code_hash"],
            hash_code(code)
        ):
            cursor.execute(
                """
                UPDATE email_verification_codes
                SET attempts = attempts + 1
                WHERE code_id = ?
                """,
                (record["code_id"],)
            )
            connection.commit()
            return False

        cursor.execute(
            """
            UPDATE admin_email_recipients
            SET is_verified = 1
            WHERE email = ?
            """,
            (email,)
        )

        cursor.execute(
            "DELETE FROM email_verification_codes WHERE email = ?",
            (email,)
        )

        connection.commit()
        return True

    finally:
        connection.close()


# --------------------------------------------------
# ADMINISTRATOR TWO-FACTOR AUTHENTICATION
# --------------------------------------------------

def send_admin_2fa_code(username, recipient_email):
    code = generate_code()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM admin_2fa_codes WHERE username = ?",
            (username,)
        )

        cursor.execute(
            """
            INSERT INTO admin_2fa_codes
            (username, code_hash, expires_at, is_used, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (
                username,
                hash_code(code),
                (current_time() + timedelta(minutes=5)).isoformat(),
                current_time().isoformat(timespec="seconds")
            )
        )

        connection.commit()

    finally:
        connection.close()

    sent = send_alert_email(
        recipient_email,
        "Smart Surveillance Admin Verification",
        f"Your administrator verification code is: {code}\n\n"
        "This code expires in 5 minutes."
    )

    if not sent:
        raise RuntimeError("Could not send administrator verification code.")

    return True



def verify_admin_2fa_code(username, code):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT code_id, code_hash, expires_at, is_used, attempts
            FROM admin_2fa_codes
            WHERE username = ?
            ORDER BY code_id DESC
            LIMIT 1
            """,
            (username,)
        )

        record = cursor.fetchone()

        if not record or record["is_used"]:
            return False

        if record["attempts"] >= 5:
            return False

        if current_time() > datetime.fromisoformat(record["expires_at"]):
            return False

        if not hmac.compare_digest(
            record["code_hash"],
            hash_code(code.strip())
        ):
            cursor.execute(
                """
                UPDATE admin_2fa_codes
                SET attempts = attempts + 1
                WHERE code_id = ?
                """,
                (record["code_id"],)
            )

            connection.commit()
            return False

        cursor.execute(
            """
            UPDATE admin_2fa_codes
            SET is_used = 1
            WHERE code_id = ?
            """,
            (record["code_id"],)
        )

        connection.commit()
        return True

    finally:
        connection.close()



# --------------------------------------------------
# VERIFIED RECIPIENT MANAGEMENT
# --------------------------------------------------

def get_verified_recipients():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT recipient_id, email, is_primary, created_at
            FROM admin_email_recipients
            WHERE is_verified = 1
            ORDER BY is_primary DESC, recipient_id ASC
            """
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def remove_email_recipient(recipient_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM admin_email_recipients
            WHERE recipient_id = ?
            """,
            (recipient_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()
