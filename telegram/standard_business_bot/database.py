import os
import sqlite3

# Calculate the database file path relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "leads.db")

def get_connection():
    """Establishes a connection to the SQLite database file."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Creates the 'leads' table if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            needs TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("Database and 'leads' table successfully initialized!")

def insert_lead(name: str, email: str, phone: str, needs: str) -> int:
    """Inserts a new lead into the database and returns the row ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leads (name, email, phone, needs)
        VALUES (?, ?, ?, ?)
    """, (name, email, phone, needs))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_all_leads() -> list:
    """Retrieves all leads from the database, ordered by creation time (newest first)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    # 1. Initialize the database and table
    init_db()
    
    # 2. Test inserting a lead
    test_id = insert_lead("Alice", "alice@example.com", "+111222333", "Needs a Telegram Business Bot")
    print(f"Test lead inserted with ID: {test_id}")
    
    # 3. Test retrieving leads to verify it works
    leads = get_all_leads()
    print("All leads in database:")
    for lead in leads:
        print(lead)
