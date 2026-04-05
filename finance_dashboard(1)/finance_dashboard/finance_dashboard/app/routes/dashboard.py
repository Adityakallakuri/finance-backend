"""
routes/dashboard.py
-------------------
GET /api/dashboard/summary  – aggregated financial overview  [analyst, admin]
"""

from flask import Blueprint, jsonify
from app.models.record import get_summary
from app.middleware.auth import roles_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("/summary")
@roles_required("analyst", "admin")
def summary():
    data = get_summary()
    return jsonify(data), 200
