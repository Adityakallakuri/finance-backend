"""
database.py
-----------
Handles SQLite connection and schema creation.
Uses raw sqlite3 (stdlib) — no ORM needed.

DATABASE_PATH env var controls the DB file location.
Set it to a temp file path in tests.
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()


def _db_path() -> str:
    """Read DB path fresh each call so tests can override via env var."""
    return os.getenv("DATABASE_PATH", "finance.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory for dict-like access."""
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _close(conn: sqlite3.Connection) -> None:
    """Close a connection. Kept as a named helper for clarity."""
    conn.close()


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users ────────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            username    TEXT UNIQUE NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'viewer',
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Financial Records ─────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id          TEXT PRIMARY KEY,
            amount      REAL NOT NULL,
            type        TEXT NOT NULL,
            category    TEXT NOT NULL,
            date        TEXT NOT NULL,
            notes       TEXT,
            created_by  TEXT NOT NULL,
            is_deleted  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    conn.commit()
    _close(conn)
    print("[DB] Tables ready.")
