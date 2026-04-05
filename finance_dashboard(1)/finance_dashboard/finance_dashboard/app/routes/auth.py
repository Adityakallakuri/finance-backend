"""
routes/auth.py
--------------
POST /api/auth/register  – create a new user account
POST /api/auth/login     – get a JWT token
GET  /api/auth/me        – get current user profile
"""

from flask import Blueprint, request, jsonify, g
from app.models.user import create_user, get_user_by_username, verify_password, safe_user
from app.middleware.auth import generate_token, jwt_required
from app.middleware.validators import validate_register

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    cleaned, error = validate_register(data)
    if error:
        return jsonify({"error": error}), 400

    # Check duplicate username
    if get_user_by_username(cleaned["username"]):
        return jsonify({"error": "Username already taken."}), 409

    try:
        user = create_user(**cleaned)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "Account created successfully.",
        "user": safe_user(user),
    }), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required."}), 400

    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid username or password."}), 401

    if not user["is_active"]:
        return jsonify({"error": "Account is deactivated. Contact an admin."}), 403

    token = generate_token(user["id"], user["role"])
    return jsonify({
        "message": "Login successful.",
        "token": token,
        "user": safe_user(user),
    }), 200


@auth_bp.get("/me")
@jwt_required
def me():
    return jsonify({"user": safe_user(g.current_user)}), 200
