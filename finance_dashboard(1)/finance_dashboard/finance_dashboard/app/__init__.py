"""
app/__init__.py
---------------
Flask application factory.
"""

from flask import Flask, jsonify
from app.database import init_db
from app.routes.auth      import auth_bp
from app.routes.users     import users_bp
from app.routes.records   import records_bp
from app.routes.dashboard import dashboard_bp


def create_app():
    app = Flask(__name__)

    # ── Register Blueprints ───────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(dashboard_bp)

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "HTTP method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error."}), 500

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "Finance Dashboard API"}), 200

    # ── Init DB on startup ────────────────────────────────────────────────────
    with app.app_context():
        init_db()

    return app
