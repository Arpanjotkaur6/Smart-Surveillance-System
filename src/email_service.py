
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load credentials from the project root .env file
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def send_alert_email(recipient, subject, body):
    """Send a surveillance alert using Gmail SMTP."""

    sender_email = os.getenv("SMTP_EMAIL")
    app_password = os.getenv("SMTP_APP_PASSWORD")

    if not sender_email or not app_password:
        print("Email configuration is missing in .env")
        return False

    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender_email, app_password)
            server.send_message(message)

        print(f"Alert email sent to {recipient}")
        return True

    except Exception as error:
        print(f"Email sending failed: {error}")
        return False
    
if __name__ == "__main__":
    recipient = input("Enter your email address for testing: ").strip()

    success = send_alert_email(
        recipient,
        "Smart Surveillance - Test Email",
        "Success! Your Smart Surveillance System email notifications are configured correctly."
    )

    print("Test successful!" if success else "Test failed.")