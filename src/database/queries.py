
from datetime import datetime

try:
    from .database import get_connection
except ImportError:
    from database import get_connection


# --------------------------------------------------
# 1. SAVE SURVEILLANCE EVENT
# --------------------------------------------------

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

    try:
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

    finally:
        connection.close()


# --------------------------------------------------
# 2. RETRIEVE RECENT EVENTS
# --------------------------------------------------

def get_recent_events(limit=10):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM surveillance_events
            ORDER BY event_time DESC, event_id DESC
            LIMIT ?
            """,
            (limit,)
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# 3. COUNT EVENTS BY OBJECT TYPE
# --------------------------------------------------

def get_event_counts():

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT object_type, COUNT(*) AS total
            FROM surveillance_events
            GROUP BY object_type
            ORDER BY total DESC
            """
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# 4. COUNT EVENTS BY CATEGORY
# --------------------------------------------------

def get_category_counts():

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                CASE
                    WHEN object_type = 'person' THEN 'person'
                    WHEN object_type IN (
                        'animal', 'bird', 'cat', 'dog', 'horse',
                        'sheep', 'cow', 'elephant', 'bear',
                        'zebra', 'giraffe'
                    ) THEN 'animal'
                    ELSE 'other'
                END AS category,
                COUNT(*) AS total
            FROM surveillance_events
            GROUP BY category
            ORDER BY total DESC
            """
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()

def get_animal_counts():
    print("DEBUG: get_animal_counts() function called!")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT LOWER(object_type) AS animal, COUNT(*) AS total
            FROM surveillance_events
            WHERE LOWER(object_type) IN (
                'animal', 'bird', 'cat', 'dog', 'horse',
                'sheep', 'cow', 'elephant', 'bear',
                'zebra', 'giraffe'
            )
            GROUP BY LOWER(object_type)
            ORDER BY total DESC
            """
        )
        results = [dict(row) for row in cursor.fetchall()]
        print("ANIMAL DATABASE RECORDS:", results)
        return results

    finally:
        connection.close()


# --------------------------------------------------
# 5. COUNT EVENTS BY EVENT TYPE
# --------------------------------------------------

def get_event_type_counts(event_type):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM surveillance_events
            WHERE LOWER(event_type) = LOWER(?)
            """,
            (event_type,)
        )

        return cursor.fetchone()["total"]

    finally:
        connection.close()


# --------------------------------------------------
# 6. SEARCH EVENTS BY PERSON NAME
# --------------------------------------------------

def search_person_events(person_name):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM surveillance_events
            WHERE LOWER(details) LIKE ?
            ORDER BY event_time DESC
            LIMIT 20
            """,
            (f"%{person_name.lower()}%",)
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# 7. FORMAT EVENT RESULTS
# --------------------------------------------------

def format_events(events):

    if not events:
        return "No matching surveillance events were found."

    lines = []

    for event in events:

        lines.append(
            f'{event["event_time"]} | '
            f'Event: {event["event_type"]} | '
            f'Object: {event["object_type"]} | '
            f'Track ID: {event["track_id"]} | '
            f'Details: {event["details"] or "N/A"}'
        )

    return "\n".join(lines)

def normalize_question(question):
    """Clean and normalize user questions."""

    question = question.lower().strip()

    replacements = {
        "persons": "person",
        "people": "person",
        "individuals": "person",
        "animals": "animal",
        "detections": "detection",
        "records": "record",
        "videos": "video",
        "unknown people": "unknown person",
        "unknown persons": "unknown person",
        "dogs": "dog",
        "cats": "cat",
        "birds": "bird",
        "cows": "cow",
        "horses": "horse",
        "sheep": "sheep",
        "elephants": "elephant",
        "bears": "bear",
        "zebras": "zebra",
        "giraffes": "giraffe",
    }

    for old, new in replacements.items():
        question = question.replace(old, new)

    return " ".join(question.rstrip("!?., ").split())

# --------------------------------------------------
# 8. NATURAL LANGUAGE QUERY SYSTEM
# --------------------------------------------------


def answer_surveillance_query(question):
    print("DEBUG: answer_surveillance_query() called!")

    if not question or not question.strip():
        return "Hello! How can I help you today?"

    normalized_question = normalize_question(question)
    question = normalized_question

    # ------------------------------------------
    # BASIC CONVERSATION
    # ------------------------------------------

    greetings = [
        "hi", "hello", "hey",
        "good morning", "good afternoon",
        "good evening"
    ]

    if normalized_question in greetings:
        return (
            "Hello! Welcome to Smart Surveillance Assistant. "
            "How can I help you today?"
        )

    if normalized_question in ["how are you", "how are you doing"]:
        return (
            "I'm doing great! I'm ready to help you "
            "monitor and understand your surveillance system."
        )

    if normalized_question in [
        "thanks", "thank you", "thank you so much"
    ]:
        return "You're welcome! I'm always here to help."

    if normalized_question in [
        "bye", "goodbye", "see you"
    ]:
        return "Goodbye! Stay safe. Have a great day!"

    if normalized_question in [
        "who are you", "what are you"
    ]:
        return (
            "I'm your Smart Surveillance Assistant. "
            "I help you understand surveillance events, "
            "person detections, animal activity, security alerts "
            "and system information."
        )

    if normalized_question in [
        "what can you do", "help", "what can i ask you"
    ]:
        return (
            "I can help you with:\\n"
            "- Person and animal detection statistics\\n"
            "- Unknown-person events\\n"
            "- Known-person entry and exit records\\n"
            "- Recent surveillance events\\n"
            "- Person activity history\\n"
            "- Security alerts and video information\\n"
            "- General information about this system\\n\\n"
            "Ask me anything about your surveillance system!"
        )

    if normalized_question in [
        "what is this system",
        "explain this system",
        "what is smart surveillance"
    ]:
        return (
            "The Smart Surveillance System uses computer vision "
            "to detect and track people, animals and other objects. "
            "It records surveillance events and videos, stores "
            "information in a database, and provides an NLP assistant "
            "to answer questions about surveillance activity."
        )
    # ------------------------------------------
    # NATURAL CASUAL CONVERSATION
    # ------------------------------------------

    # What are you doing?
    if any(phrase in question for phrase in [
        "what are you doing",
        "what are u doing",
        "what are you up to",
        "are you busy",
        "what is happening",
        "what's happening",
        "whats happening"
    ]):
        return (
            "I'm here, keeping an eye on surveillance activity "
            "and ready to answer your questions! What would you "
            "like to talk about?"
        )

    # Personal questions
    if any(phrase in question for phrase in [
        "do you have a name",
        "what is your name",
        "whats your name",
        "what's your name"
    ]):
        return (
            "You can call me Surveillance Assistant! "
            "I'm your digital security companion."
        )

    if any(phrase in question for phrase in [
        "who created you",
        "who made you",
        "who developed you",
        "who built you"
    ]):
        return (
            "I was developed as part of the Smart Surveillance "
            "System project to make security monitoring easier "
            "and more interactive."
        )

    if any(phrase in question for phrase in [
        "do you sleep",
        "are you real",
        "are you human",
        "are you a robot"
    ]):
        return (
            "I'm an AI-based software assistant, not a human. "
            "I don't need sleep, so I'm always ready when "
            "the system is running!"
        )

    # Casual conversation
    if any(phrase in question for phrase in [
        "are you bored",
        "im bored",
        "i am bored",
        "lets talk",
        "let's talk",
        "can we talk",
        "talk to me"
    ]):
        return (
            "Of course! I'm happy to chat. We can talk about "
            "technology, security, interesting facts, or anything "
            "else you'd like."
        )

    if any(phrase in question for phrase in [
        "tell me something interesting",
        "say something interesting",
        "surprise me"
    ]):
        return (
            "Here's something interesting: computer vision "
            "systems can track objects across video frames, "
            "helping distinguish a continuously visible object "
            "from a newly appearing one!"
        )

    # Compliments
    if any(phrase in question for phrase in [
        "you are funny",
        "you are amazing",
        "you are helpful",
        "good job",
        "well done",
        "nice work"
    ]):
        return (
            "Thank you! I'm glad I could help. "
            "Let's make this surveillance system even better!"
        )

    # Apologies
    if any(phrase in question for phrase in [
        "sorry",
        "my bad",
        "i made a mistake"
    ]):
        return (
            "No worries! Everyone makes mistakes. "
            "How can I help you?"
        )

    # Repeat or simplify
    if any(phrase in question for phrase in [
        "repeat that",
        "say that again",
        "explain again",
        "explain simply",
        "make it simpler",
        "i dont understand",
        "i don't understand"
    ]):
        return (
            "Of course! Tell me which part you'd like explained, "
            "and I'll try to make it simpler."
        )

    # General help
    if any(phrase in question for phrase in [
        "guide me",
        "help me get started",
        "where should i start",
        "i dont know what to ask",
        "i don't know what to ask"
    ]):
        return (
            "No problem! You can ask me about recent activity, "
            "people, unknown visitors, animals, video recordings, "
            "or anything about how this surveillance system works."
        )

    # Asking for an opinion
    if any(phrase in question for phrase in [
        "what do you think",
        "your opinion",
        "do you agree"
    ]):
        return (
            "I can help you think through that! Tell me a little "
            "more about what you're considering."
        )
    

    # Category breakdown
    if any(word in question for word in [
        "category", "categories", "breakdown"
    ]):
        counts = get_category_counts()

        if not counts:
            return "No surveillance events have been recorded."

        return "\n".join(
            f'{item["category"].title()}: {item["total"]}'
            for item in counts
        )

    # Unknown persons
    if any(phrase in question for phrase in [
        "unknown",
        "stranger",
        "unauthorized",
        "unrecognized",
        "unidentified"
    ]):
        total = get_event_type_counts("unknown_person")

        if any(word in question for word in [
            "recent", "latest", "show", "list", "when"
        ]):
            events = [
                event for event in get_recent_events(1000)
                if event["event_type"] == "unknown_person"
            ]
            return format_events(events)

        return f"Total unknown-person events recorded: {total}"
    
    # Known-person entries
    if "known" in question and any(
        word in question for word in ["entry", "enter"]
    ):
        return (
            "Total known-person entries recorded: "
            f'{get_event_type_counts("known_person_entry")}'
        )

    # Known-person exits
    if "known" in question and any(
        word in question for word in ["exit", "left"]
    ):
        return (
            "Total known-person exits recorded: "
            f'{get_event_type_counts("known_person_exit")}'
        )

    # Person history
    if "history of" in question or "events of" in question:
        name = (
            question.split("history of")[-1]
            if "history of" in question
            else question.split("events of")[-1]
        )

        name = name.replace("?", "").strip()

        return format_events(search_person_events(name))

    # Animal queries
    # Animal queries
    # Animal-specific queries
    # Animal-specific queries
    animal_names = [
        "dog", "cat", "bird", "cow", "horse",
        "sheep", "elephant", "bear", "zebra",
        "giraffe"
    ]

    animal_counts = get_animal_counts()

    requested_animal = next(
        (animal for animal in animal_names
        if animal in question.split()),
        None
    )

    # Recent animal detections
    # Recent animal detections
    if "animal" in question or requested_animal:

        if any(word in question for word in [
            "recent", "latest", "show", "list", "when", "history"
        ]):
            events = [
                event for event in get_recent_events(1000)
                if (event["object_type"] or "").lower() in animal_names
                or (event["object_type"] or "").lower() == "animal"
            ]

            if requested_animal:
                events = [
                    event for event in events
                    if (event["object_type"] or "").lower() == requested_animal
                    or (event["object_type"] or "").lower() == "animal"
                ]

            if not events:
                return "No animal detection records found."

            return format_events(events)

        if requested_animal:
            total = next(
                (item["total"] for item in animal_counts
                if item["animal"] == requested_animal),
                0
            )

            return f"Total {requested_animal} detections recorded: {total}"

        total = sum(item["total"] for item in animal_counts)
        return f"Total animal events recorded: {total}"
    # Recent events
    if any(word in question for word in [
        "recent", "latest", "last events"
    ]):
        return format_events(get_recent_events(10))

    # General counts
    if any(word in question for word in [
        "how many", "count", "total"
    ]):
        counts = get_event_counts()

        if not counts:
            return "No surveillance events have been recorded."

        return "\n".join(
            f'{item["object_type"].title()}: {item["total"]} events'
            for item in counts
        )

    return (
        "I could not understand that surveillance query. "
        "Try asking about people, animals, unknown persons, "
        "known entries, exits, category breakdown, or recent events."
    )
