"""
middleware/validators.py
------------------------
Simple validation helpers that return (data, error_message).
If error_message is not None, the request should be rejected.
"""

import re
from datetime import date


def validate_register(data: dict):
    username = (data.get("username") or "").strip()
    email    = (data.get("email") or "").strip()
    password = data.get("password", "")
    role     = data.get("role", "viewer")

    if not username or len(username) < 3:
        return None, "username must be at least 3 characters."
    if not re.match(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$", email):
        return None, "Invalid email address."
    if len(password) < 6:
        return None, "password must be at least 6 characters."
    if role not in ("viewer", "analyst", "admin"):
        return None, "role must be viewer, analyst, or admin."

    return {"username": username, "email": email, "password": password, "role": role}, None


def validate_record(data: dict):
    errors = []

    # amount
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            errors.append("amount must be a positive number.")
    except (TypeError, ValueError):
        errors.append("amount must be a valid number.")
        amount = None

    # type
    type_ = data.get("type", "")
    if type_ not in ("income", "expense"):
        errors.append("type must be 'income' or 'expense'.")

    # category
    category = (data.get("category") or "").strip()
    if not category:
        errors.append("category is required.")

    # date
    date_str = data.get("date", "")
    try:
        date.fromisoformat(date_str)   # validates YYYY-MM-DD format
    except ValueError:
        errors.append("date must be a valid ISO date (YYYY-MM-DD).")

    if errors:
        return None, "; ".join(errors)

    return {
        "amount":   amount,
        "type_":    type_,
        "category": category,
        "date":     date_str,
        "notes":    (data.get("notes") or "").strip(),
    }, None
