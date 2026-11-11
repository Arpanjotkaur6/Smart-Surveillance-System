from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Query, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from fastapi import HTTPException
from database.auth import verify_admin
import base64
import numpy as np
import cv2

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174"
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
