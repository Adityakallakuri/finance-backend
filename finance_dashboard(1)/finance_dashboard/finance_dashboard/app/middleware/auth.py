"""
middleware/auth.py
------------------
JWT-based authentication and role-based access control decorators.

Usage in routes:
    @jwt_required          – any logged-in user
    @roles_required("admin")           – only admins
    @roles_required("admin", "analyst") – admin OR analyst
"""

import os
import jwt
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import request, jsonify, g
from app.models.user import get_user_by_id
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 24))


# ── Token Generation ──────────────────────────────────────────────────────────

def generate_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ── Decode & Validate ─────────────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


# ── Decorators ────────────────────────────────────────────────────────────────

def jwt_required(f):
    """Verify JWT and load current user into flask.g."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or malformed."}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        user = get_user_by_id(payload["sub"])
        if not user:
            return jsonify({"error": "User not found."}), 401
        if not user["is_active"]:
            return jsonify({"error": "Account is deactivated."}), 403

        g.current_user = user   # available throughout the request
        return f(*args, **kwargs)
    return wrapper


def roles_required(*allowed_roles):
    """Only allow users whose role is in allowed_roles."""
    def decorator(f):
        @wraps(f)
        @jwt_required
        def wrapper(*args, **kwargs):
            if g.current_user["role"] not in allowed_roles:
                return jsonify({
                    "error": f"Access denied. Required role(s): {list(allowed_roles)}"
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
