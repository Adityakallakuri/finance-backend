"""
routes/records.py
-----------------
GET    /api/records           – list records (paginated + filtered)   [viewer, analyst, admin]
POST   /api/records           – create a record                       [admin]
GET    /api/records/<id>      – get a single record                   [viewer, analyst, admin]
PUT    /api/records/<id>      – update a record                       [admin]
DELETE /api/records/<id>      – soft delete a record                  [admin]
"""

from flask import Blueprint, request, jsonify, g
from app.models.record import (
    create_record, get_record_by_id, get_records,
    update_record, soft_delete_record,
)
from app.middleware.auth import jwt_required, roles_required
from app.middleware.validators import validate_record

records_bp = Blueprint("records", __name__, url_prefix="/api/records")


@records_bp.get("/")
@jwt_required
def list_records():
    # Build filters from query params
    filters = {}
    for key in ("type", "category", "date_from", "date_to"):
        val = request.args.get(key)
        if val:
            filters[key] = val

    # Pagination
    try:
        page     = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError:
        return jsonify({"error": "page and per_page must be integers."}), 400

    result = get_records(filters=filters, page=page, per_page=per_page)
    return jsonify(result), 200


@records_bp.post("/")
@roles_required("admin")
def create():
    data = request.get_json(silent=True) or {}
    cleaned, error = validate_record(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        record = create_record(**cleaned, created_by=g.current_user["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "Record created.", "record": record}), 201


@records_bp.get("/<record_id>")
@jwt_required
def get_one(record_id):
    record = get_record_by_id(record_id)
    if not record:
        return jsonify({"error": "Record not found."}), 404
    return jsonify({"record": record}), 200


@records_bp.put("/<record_id>")
@roles_required("admin")
def update(record_id):
    record = get_record_by_id(record_id)
    if not record:
        return jsonify({"error": "Record not found."}), 404

    data = request.get_json(silent=True) or {}
    # Only validate fields that are being updated
    if not data:
        return jsonify({"error": "No update data provided."}), 400

    # Partial validation: if type or amount provided, check them
    if "type" in data and data["type"] not in ("income", "expense"):
        return jsonify({"error": "type must be 'income' or 'expense'."}), 400
    if "amount" in data:
        try:
            val = float(data["amount"])
            if val <= 0:
                return jsonify({"error": "amount must be a positive number."}), 400
            data["amount"] = val
        except (TypeError, ValueError):
            return jsonify({"error": "amount must be a valid number."}), 400

    try:
        updated = update_record(record_id, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "Record updated.", "record": updated}), 200


@records_bp.delete("/<record_id>")
@roles_required("admin")
def delete(record_id):
    deleted = soft_delete_record(record_id)
    if not deleted:
        return jsonify({"error": "Record not found."}), 404
    return jsonify({"message": "Record deleted successfully."}), 200
