"""
routes/users.py
---------------
GET    /api/users          – list all users          [admin]
GET    /api/users/<id>     – get a single user       [admin]
PUT    /api/users/<id>     – update role/status      [admin]
"""

from flask import Blueprint, request, jsonify
from app.models.user import get_all_users, get_user_by_id, update_user, safe_user
from app.middleware.auth import roles_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.get("/")
@roles_required("admin")
def list_users():
    users = get_all_users()
    return jsonify({
        "users": [safe_user(u) for u in users],
        "total": len(users),
    }), 200


@users_bp.get("/<user_id>")
@roles_required("admin")
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": safe_user(user)}), 200


@users_bp.put("/<user_id>")
@roles_required("admin")
def update_user_route(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    allowed_fields = {}

    if "role" in data:
        if data["role"] not in ("viewer", "analyst", "admin"):
            return jsonify({"error": "Invalid role."}), 400
        allowed_fields["role"] = data["role"]

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "is_active must be true or false."}), 400
        allowed_fields["is_active"] = int(data["is_active"])

    if not allowed_fields:
        return jsonify({"error": "Provide 'role' or 'is_active' to update."}), 400

    try:
        updated = update_user(user_id, allowed_fields)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "User updated.", "user": safe_user(updated)}), 200
