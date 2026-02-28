# database/manager.py
import sqlite3
import json
import os
from datetime import datetime, date
from contextlib import contextmanager
from typing import Optional

DB_PATH = "database/bot.db"

# ─────────────────────────────────────────────────────────────
#  Schema
# ─────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY,
    username       TEXT,
    full_name      TEXT    NOT NULL,
    astrites       INTEGER NOT NULL DEFAULT 1600,
    aura           INTEGER NOT NULL DEFAULT 0,
    total_pulls    INTEGER NOT NULL DEFAULT 0,
    celestia_pity  INTEGER NOT NULL DEFAULT 0,
    arcborne_pity  INTEGER NOT NULL DEFAULT 0,
    luck_rate      REAL    NOT NULL DEFAULT 0.0,
    created_at     TEXT    NOT NULL,
    last_daily     TEXT
);

CREATE TABLE IF NOT EXISTS user_cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(user_id),
    card_code   TEXT    NOT NULL,
    obtained_at TEXT    NOT NULL,
    UNIQUE(user_id, card_code)
);

CREATE TABLE IF NOT EXISTS pull_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(user_id),
    card_code   TEXT    NOT NULL,
    pull_type   TEXT    NOT NULL,   -- 'single' | 'multi'
    pulled_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_cards    ON user_cards(user_id);
CREATE INDEX IF NOT EXISTS idx_pull_history  ON pull_history(user_id);
"""


@contextmanager
def get_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


# ─────────────────────────────────────────────────────────────
#  User CRUD
# ─────────────────────────────────────────────────────────────
def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()


def create_user(user_id: int, username: Optional[str], full_name: str) -> sqlite3.Row:
    from config import config
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO users
               (user_id, username, full_name, astrites, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, full_name, config.STARTING_ASTRITES,
             datetime.now().isoformat())
        )
    return get_user(user_id)


def get_or_create_user(user_id: int, username: Optional[str], full_name: str):
    user = get_user(user_id)
    if not user:
        user = create_user(user_id, username, full_name)
    return user


def update_user_stats(user_id: int, **kwargs):
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    with get_db() as conn:
        conn.execute(f"UPDATE users SET {sets} WHERE user_id = ?", vals)


# ─────────────────────────────────────────────────────────────
#  Cards
# ─────────────────────────────────────────────────────────────
def get_user_cards(user_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT card_code FROM user_cards WHERE user_id = ? ORDER BY obtained_at",
            (user_id,)
        ).fetchall()
    return [r["card_code"] for r in rows]


def add_card_to_user(user_id: int, card_code: str) -> bool:
    """Returns True if new card, False if duplicate."""
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO user_cards (user_id, card_code, obtained_at) VALUES (?, ?, ?)",
                (user_id, card_code, datetime.now().isoformat())
            )
            return True
        except sqlite3.IntegrityError:
            return False


def has_card(user_id: int, card_code: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM user_cards WHERE user_id = ? AND card_code = ?",
            (user_id, card_code)
        ).fetchone()
    return row is not None


def count_user_cards(user_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM user_cards WHERE user_id = ?",
            (user_id,)
        ).fetchone()
    return row["cnt"]


# ─────────────────────────────────────────────────────────────
#  Pull history
# ─────────────────────────────────────────────────────────────
def log_pull(user_id: int, card_code: str, pull_type: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO pull_history (user_id, card_code, pull_type, pulled_at) VALUES (?, ?, ?, ?)",
            (user_id, card_code, pull_type, datetime.now().isoformat())
        )


# ─────────────────────────────────────────────────────────────
#  Daily reward
# ─────────────────────────────────────────────────────────────
def claim_daily(user_id: int, reward_amount: int) -> bool:
    """Returns True if claimed, False if already claimed today."""
    today = date.today().isoformat()
    user = get_user(user_id)
    if not user:
        return False
    if user["last_daily"] == today:
        return False
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET astrites = astrites + ?, last_daily = ? WHERE user_id = ?",
            (reward_amount, today, user_id)
        )
    return True


# ─────────────────────────────────────────────────────────────
#  Leaderboard
# ─────────────────────────────────────────────────────────────
def get_leaderboard(limit: int = 10) -> list:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT u.full_name, u.total_pulls,
                      COUNT(uc.card_code) as card_count
               FROM users u
               LEFT JOIN user_cards uc ON u.user_id = uc.user_id
               GROUP BY u.user_id
               ORDER BY card_count DESC, u.total_pulls DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
