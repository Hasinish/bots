import os
import sqlite3

# Calculate database file path relative to database.py location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "leads.db")

def get_connection():
    """Get SQLite connection."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes tables for leads and user settings."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create leads table with language column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            needs TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create user settings table to persist language preference
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            chat_id INTEGER PRIMARY KEY,
            language TEXT NOT NULL DEFAULT 'en',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database tables initialized successfully! :)")

def insert_lead(name: str, email: str, phone: str, needs: str, language: str = 'en') -> int:
    """Inserts a new lead into SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leads (name, email, phone, needs, language)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, phone, needs, language))
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id

def get_all_leads() -> list:
    """Fetches all registered leads, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def set_user_language(chat_id: int, language: str):
    """Sets or updates the preferred language for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_settings (chat_id, language, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(chat_id) DO UPDATE SET
            language = excluded.language,
            updated_at = CURRENT_TIMESTAMP
    """, (chat_id, language))
    conn.commit()
    conn.close()

def get_user_language(chat_id: int) -> str:
    """Gets the user's language setting. Defaults to 'en'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM user_settings WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 'en'

if __name__ == "__main__":
    init_db()
