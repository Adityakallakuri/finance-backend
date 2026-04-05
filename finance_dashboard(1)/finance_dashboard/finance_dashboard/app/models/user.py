"""
models/user.py
--------------
All database operations related to Users.
"""

import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_connection, _close

ROLES = ("viewer", "analyst", "admin")


def _row_to_dict(row):
    return dict(row) if row else None


def create_user(username: str, email: str, password: str, role: str = "viewer") -> dict:
    if role not in ROLES:
        raise ValueError(f"Invalid role '{role}'. Choose from {ROLES}.")

    user_id = str(uuid.uuid4())
    hashed_pw = generate_password_hash(password)

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (id, username, email, password, role) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, email, hashed_pw, role),
        )
        conn.commit()
    finally:
        _close(conn)

    return get_user_by_id(user_id)


def get_user_by_id(user_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    _close(conn)
    return _row_to_dict(row)


def get_user_by_username(username: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    _close(conn)
    return _row_to_dict(row)


def get_all_users() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    _close(conn)
    return [_row_to_dict(r) for r in rows]


def update_user(user_id: str, updates: dict) -> dict | None:
    allowed = {"role", "is_active", "email"}
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        raise ValueError("No valid fields to update.")

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]

    conn = get_connection()
    conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    conn.commit()
    _close(conn)
    return get_user_by_id(user_id)


def verify_password(plain: str, hashed: str) -> bool:
    return check_password_hash(hashed, plain)


def safe_user(user: dict) -> dict:
    """Return user dict without the password field."""
    return {k: v for k, v in user.items() if k != "password"}
