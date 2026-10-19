
import sqlite3
from pathlib import Path

# Find the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Store the database in the project root
DATABASE_PATH = PROJECT_ROOT / "surveillance.db"


def get_connection():
    """Create and return a connection to the surveillance database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


if __name__ == "__main__":
    connection = get_connection()
    print("Database connected successfully!")
    print(f"Database location: {DATABASE_PATH}")
    connection.close()
