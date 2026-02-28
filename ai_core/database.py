# ai_core/database.py
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "data/ai_history.db"

@contextmanager
def get_ai_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_ai_db():
    with get_ai_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def add_to_history(user_id: int, role: str, content: str):
    with get_ai_db() as conn:
        conn.execute("INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)", 
                    (user_id, role, content))

def get_recent_history(user_id: int, limit: int = 10):
    with get_ai_db() as conn:
        cursor = conn.execute(
            "SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", 
            (user_id, limit)
        )
        history = cursor.fetchall()
    return list(reversed([(r["role"], r["content"]) for r in history]))

# Initialize on import
init_ai_db()
