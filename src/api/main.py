import os
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from pydantic import BaseModel
from pathlib import Path
from fastapi import HTTPException
from database.auth import verify_admin
from database.email_manager import (
    add_email_recipient,
    verify_email_recipient,
    send_admin_2fa_code,
    verify_admin_2fa_code,
    get_verified_recipients,
    remove_email_recipient
)
import base64
import numpy as np
import cv2
import secrets
import time
from fastapi import Header

from face_recognition.face_detector import FaceDetector
from face_recognition.face_recognizer import FaceRecognizer
from face_recognition.person_manager import save_authorized_person

from database.database import get_connection
from database.queries import (
    get_recent_events,
    get_event_counts,
    get_category_counts,
    get_event_type_counts,
    answer_surveillance_query
)
from nlp.llm import ask_gemma
security = HTTPBasic()
def verify_admin_access(
    credentials: HTTPBasicCredentials = Depends(security)
):
    if not verify_admin(credentials.username, credentials.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid administrator credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
app = FastAPI(
    title="Smart Surveillance System API",
    description="Backend API for surveillance events, statistics, videos and NLP queries",
    version="1.0.0"
)
# --------------------------------------------------
# ADMINISTRATOR TWO-FACTOR SESSIONS
# --------------------------------------------------

admin_2fa_sessions = {}

ADMIN_SESSION_DURATION = 600  # 10 minutes


def create_admin_session(username):
    token = secrets.token_urlsafe(32)

    admin_2fa_sessions[token] = {
        "username": username,
        "expires_at": time.time() + ADMIN_SESSION_DURATION
    }

    return token


def verify_admin_session(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Administrator 2FA session required."
        )

    token = credentials.credentials

    session = admin_2fa_sessions.get(token)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Invalid administrator session."
        )

    if time.time() > session["expires_at"]:
        admin_2fa_sessions.pop(token, None)

        raise HTTPException(
            status_code=401,
            detail="Administrator session expired. Please verify again."
        )

    return session["username"]
    

app.mount(
    "/recordings",
    StaticFiles(directory="recordings"),
    name="recordings"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class SurveillanceQuery(BaseModel):
    question: str

class PersonRegistration(BaseModel):
    person_name: str
    image: str    

class EmailRequest(BaseModel):
    email: str


class EmailVerificationRequest(BaseModel):
    email: str
    code: str


class Admin2FARequest(BaseModel):
    username: str
    password: str


class Admin2FAVerificationRequest(BaseModel):
    username: str
    code: str


# --------------------------------------------------
# ADMINISTRATOR TWO-FACTOR AUTHENTICATION
# --------------------------------------------------

@app.post("/api/admin/2fa/request")
def request_admin_2fa(request: Admin2FARequest):

    if not verify_admin(request.username, request.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid administrator credentials."
        )

    recipient = os.getenv("SMTP_EMAIL")
    if not recipient:
        raise HTTPException(
            status_code=400,
            detail="No administrator email is configured."
        )

    try:
        send_admin_2fa_code(request.username, recipient)

        return {
            "message": "Administrator verification code sent."
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not send administrator verification code."
        )


@app.post("/api/admin/2fa/verify")
def verify_admin_2fa(request: Admin2FAVerificationRequest):

    if not verify_admin_2fa_code(request.username, request.code):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired verification code."
        )

    token = create_admin_session(request.username)

    return {
        "message": "Administrator verification successful.",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ADMIN_SESSION_DURATION
    }


# --------------------------------------------------
# PROTECTED EMAIL RECIPIENT MANAGEMENT
# --------------------------------------------------

@app.get("/api/admin/emails")
def list_admin_emails(
    admin: str = Depends(verify_admin_session)
):
    return {
        "recipients": get_verified_recipients()
    }


@app.post("/api/admin/emails/request-verification")
def request_email_verification(
    request: EmailRequest,
    admin: str = Depends(verify_admin_session)
):
    try:
        return add_email_recipient(request.email)

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not send email verification code."
        )


@app.post("/api/admin/emails/verify")
def verify_email(
    request: EmailVerificationRequest,
    admin: str = Depends(verify_admin_session)
):
    if not verify_email_recipient(request.email, request.code):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired email verification code."
        )

    return {
        "message": "Email address verified successfully."
    }


@app.delete("/api/admin/emails/{recipient_id}")
def delete_admin_email(
    recipient_id: int,
    admin: str = Depends(verify_admin_session)
):
    if not remove_email_recipient(recipient_id):
        raise HTTPException(
            status_code=404,
            detail="Email recipient not found."
        )

    return {
        "message": "Email recipient removed successfully."
    }


# --------------------------------------------------
# HOME AND HEALTH
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Smart Surveillance System API is running",
        "status": "active"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# DATABASE CONNECTION CHECK
# --------------------------------------------------

@app.get("/api/database/status")
def database_status():

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")

        return {
            "database": "connected",
            "status": "healthy"
        }

    finally:
        connection.close()


# --------------------------------------------------
# AUTHORIZED PERSONS
# --------------------------------------------------

@app.get("/api/persons")
def get_authorized_persons(
    admin: str = Depends(verify_admin_access)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT person_id, person_name, created_at
            FROM authorized_persons
            ORDER BY created_at DESC
        """)

        persons = [dict(row) for row in cursor.fetchall()]

        return {
            "total_persons": len(persons),
            "persons": persons
        }

    finally:
        connection.close()


# --------------------------------------------------
# REGISTER AUTHORIZED PERSON
# --------------------------------------------------

@app.post("/api/persons")
def register_authorized_person(
    person: PersonRegistration,
    admin: str = Depends(verify_admin_access)
):
    try:
        image_data = person.image.split(",", 1)[-1]
        image_bytes = base64.b64decode(image_data, validate=True)

        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid face image.")

        detector = FaceDetector()
        faces = detector.detect(frame)

        if faces is None or len(faces) == 0:
            raise HTTPException(status_code=400, detail="No face detected.")

        if len(faces) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple faces detected. Only one person should be visible."
            )

        recognizer = FaceRecognizer()
        embedding = recognizer.get_embedding(frame, faces[0])

        save_authorized_person(person.person_name, embedding)

        return {
            "message": f"{person.person_name} registered successfully."
        }

    except HTTPException:
        raise

    except (ValueError, base64.binascii.Error) as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Person registration failed: {str(error)}"
        )



# --------------------------------------------------
# SURVEILLANCE EVENTS
# --------------------------------------------------

@app.get("/api/events")
def get_events(limit: int = Query(default=20, ge=1, le=500)):

    events = get_recent_events(limit)

    return {
        "total_returned": len(events),
        "events": events
    }


# --------------------------------------------------
# EVENT STATISTICS
# --------------------------------------------------

@app.get("/api/statistics")
def get_statistics():

    return {
        "object_counts": get_event_counts(),
        "category_counts": get_category_counts(),
        "unknown_person_count": get_event_type_counts("unknown_person")
    }


# --------------------------------------------------
# VIDEO RECORDINGS
# --------------------------------------------------

@app.get("/api/videos")
def get_videos():


    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM video_recordings
            ORDER BY created_at DESC
            """
        )

        videos = [dict(row) for row in cursor.fetchall()]

        return {
            "total_videos": len(videos),
            "videos": videos
        }

    finally:
        connection.close()


# --------------------------------------------------
# NATURAL LANGUAGE QUERY
# --------------------------------------------------
@app.post("/api/query")
def surveillance_query(request: SurveillanceQuery):

    question = request.question.strip()

    # First, try the existing surveillance database
    answer = answer_surveillance_query(question)

    # If the database cannot understand the question,
    # use Gemma for natural conversation and general questions
    if answer.startswith("I could not understand that surveillance query"):
        answer = ask_gemma(question)

    return {
        "question": question,
        "answer": answer
    }


# --------------------------------------------------
# DELETE A VIDEO RECORDING
# --------------------------------------------------


@app.delete("/api/videos/{video_id}")
def delete_video(
    video_id: int,
    admin: str = Depends(verify_admin_session)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT video_id, file_path
            FROM video_recordings
            WHERE video_id = ?
            """,
            (video_id,)
        )

        video = cursor.fetchone()

        if video is None:
            raise HTTPException(
                status_code=404,
                detail="Video recording not found."
            )

        project_root = Path(__file__).resolve().parents[2]
        recordings_dir = (project_root / "recordings").resolve()

        video_path = Path(video["file_path"])

        if not video_path.is_absolute():
            video_path = project_root / video_path

        video_path = video_path.resolve()

        if recordings_dir not in video_path.parents:
            raise HTTPException(
                status_code=400,
                detail="Invalid recording file path."
            )

        if video_path.is_file():
            video_path.unlink()

        cursor.execute(
            "DELETE FROM video_recordings WHERE video_id = ?",
            (video_id,)
        )

        connection.commit()

        return {
            "message": "Video recording deleted successfully."
        }

    finally:
        connection.close()