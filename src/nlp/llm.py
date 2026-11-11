
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma4:e2b"


def ask_gemma(question, conversation_history=None):
    """Send a question to Gemma and return its response."""

    messages = [
        {
            "role": "system",
            "content": (
                "You are the conversational AI assistant for a Smart "
                "Surveillance System. Be friendly, helpful, and natural. "
                "Answer everyday questions and general knowledge questions. "
                "You can explain the system's features, but never invent "
                "surveillance events, counts, identities, or timestamps. "
                "For actual surveillance records, rely on the system's "
                "database rather than guessing."
            )
        }
    ]

    if conversation_history:
        messages.extend(conversation_history[-10:])

    messages.append({
        "role": "user",
        "content": question
    })

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        return result["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "The AI is taking too long to respond. Please try again."

    except requests.exceptions.ConnectionError:
        return "I cannot connect to the local AI model. Please check whether Ollama is running."

    except requests.exceptions.RequestException as error:
        print("Ollama API Error:", error)
        return "Sorry, I encountered a problem while generating a response."
