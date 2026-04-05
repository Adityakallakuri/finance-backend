"""
tests/test_api.py
-----------------
Integration tests covering auth, records, users, and dashboard endpoints.
Run with: python -m pytest tests/ -v
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.database import init_db, DB_PATH


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Use an in-memory test DB so tests never touch finance.db"""
    import app.database as db_module
    db_module.DB_PATH = ":memory:"          # redirect to RAM

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def login(client, username, password):
    res = client.post("/api/auth/login",
                      json={"username": username, "password": password})
    return res.get_json()["token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        res = client.post("/api/auth/register", json={
            "username": "testadmin",
            "email": "testadmin@test.com",
            "password": "secret123",
            "role": "admin",
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["user"]["username"] == "testadmin"
        assert "password" not in data["user"]

    def test_register_duplicate_username(self, client):
        client.post("/api/auth/register", json={
            "username": "dupuser", "email": "dup@test.com",
            "password": "pass123", "role": "viewer",
        })
        res = client.post("/api/auth/register", json={
            "username": "dupuser", "email": "dup2@test.com",
            "password": "pass123", "role": "viewer",
        })
        assert res.status_code == 409

    def test_register_invalid_email(self, client):
        res = client.post("/api/auth/register", json={
            "username": "baduser", "email": "not-an-email",
            "password": "pass123", "role": "viewer",
        })
        assert res.status_code == 400

    def test_login_success(self, client):
        res = client.post("/api/auth/login",
                          json={"username": "testadmin", "password": "secret123"})
        assert res.status_code == 200
        assert "token" in res.get_json()

    def test_login_wrong_password(self, client):
        res = client.post("/api/auth/login",
                          json={"username": "testadmin", "password": "wrongpass"})
        assert res.status_code == 401

    def test_me_endpoint(self, client):
        token = login(client, "testadmin", "secret123")
        res = client.get("/api/auth/me", headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["user"]["username"] == "testadmin"

    def test_me_without_token(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401


# ── Records Tests ─────────────────────────────────────────────────────────────

class TestRecords:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        # Create roles
        client.post("/api/auth/register", json={
            "username": "rec_admin", "email": "ra@test.com",
            "password": "admin123", "role": "admin",
        })
        client.post("/api/auth/register", json={
            "username": "rec_viewer", "email": "rv@test.com",
            "password": "viewer123", "role": "viewer",
        })
        self.admin_token  = login(client, "rec_admin",  "admin123")
        self.viewer_token = login(client, "rec_viewer", "viewer123")

    def test_create_record_as_admin(self, client):
        res = client.post("/api/records/", headers=auth_header(self.admin_token),
                          json={
                              "amount": 1500.0, "type": "income",
                              "category": "Salary", "date": "2024-01-01",
                              "notes": "Jan salary",
                          })
        assert res.status_code == 201
        assert res.get_json()["record"]["amount"] == 1500.0

    def test_viewer_cannot_create_record(self, client):
        res = client.post("/api/records/", headers=auth_header(self.viewer_token),
                          json={
                              "amount": 100.0, "type": "expense",
                              "category": "Food", "date": "2024-01-02",
                          })
        assert res.status_code == 403

    def test_invalid_record_missing_fields(self, client):
        res = client.post("/api/records/", headers=auth_header(self.admin_token),
                          json={"amount": -50, "type": "income"})
        assert res.status_code == 400

    def test_list_records_as_viewer(self, client):
        res = client.get("/api/records/", headers=auth_header(self.viewer_token))
        assert res.status_code == 200
        assert "records" in res.get_json()

    def test_filter_by_type(self, client):
        res = client.get("/api/records/?type=income",
                         headers=auth_header(self.viewer_token))
        assert res.status_code == 200
        for r in res.get_json()["records"]:
            assert r["type"] == "income"

    def test_pagination(self, client):
        res = client.get("/api/records/?page=1&per_page=5",
                         headers=auth_header(self.viewer_token))
        data = res.get_json()
        assert res.status_code == 200
        assert "total_pages" in data

    def test_update_record(self, client):
        # Create first
        create_res = client.post("/api/records/",
                                  headers=auth_header(self.admin_token),
                                  json={"amount": 200.0, "type": "expense",
                                        "category": "Food", "date": "2024-02-01"})
        record_id = create_res.get_json()["record"]["id"]

        # Update
        res = client.put(f"/api/records/{record_id}",
                         headers=auth_header(self.admin_token),
                         json={"amount": 250.0, "notes": "updated"})
        assert res.status_code == 200
        assert res.get_json()["record"]["amount"] == 250.0

    def test_delete_record(self, client):
        create_res = client.post("/api/records/",
                                  headers=auth_header(self.admin_token),
                                  json={"amount": 99.0, "type": "expense",
                                        "category": "Misc", "date": "2024-03-01"})
        record_id = create_res.get_json()["record"]["id"]

        res = client.delete(f"/api/records/{record_id}",
                            headers=auth_header(self.admin_token))
        assert res.status_code == 200

        # Should not be visible anymore
        get_res = client.get(f"/api/records/{record_id}",
                             headers=auth_header(self.viewer_token))
        assert get_res.status_code == 404


# ── Dashboard Tests ───────────────────────────────────────────────────────────

class TestDashboard:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        client.post("/api/auth/register", json={
            "username": "dash_analyst", "email": "da@test.com",
            "password": "analyst123", "role": "analyst",
        })
        client.post("/api/auth/register", json={
            "username": "dash_viewer2", "email": "dv2@test.com",
            "password": "viewer123", "role": "viewer",
        })
        self.analyst_token = login(client, "dash_analyst", "analyst123")
        self.viewer_token  = login(client, "dash_viewer2", "viewer123")

    def test_summary_accessible_by_analyst(self, client):
        res = client.get("/api/dashboard/summary",
                         headers=auth_header(self.analyst_token))
        assert res.status_code == 200
        data = res.get_json()
        assert "total_income"   in data
        assert "total_expenses" in data
        assert "net_balance"    in data
        assert "by_category"    in data
        assert "monthly_trends" in data

    def test_viewer_cannot_access_dashboard(self, client):
        res = client.get("/api/dashboard/summary",
                         headers=auth_header(self.viewer_token))
        assert res.status_code == 403


# ── User Management Tests ─────────────────────────────────────────────────────

class TestUsers:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        client.post("/api/auth/register", json={
            "username": "mgmt_admin", "email": "ma@test.com",
            "password": "admin123", "role": "admin",
        })
        client.post("/api/auth/register", json={
            "username": "mgmt_viewer", "email": "mv@test.com",
            "password": "viewer123", "role": "viewer",
        })
        self.admin_token  = login(client, "mgmt_admin",  "admin123")
        self.viewer_token = login(client, "mgmt_viewer", "viewer123")

    def test_admin_can_list_users(self, client):
        res = client.get("/api/users/", headers=auth_header(self.admin_token))
        assert res.status_code == 200
        assert "users" in res.get_json()

    def test_viewer_cannot_list_users(self, client):
        res = client.get("/api/users/", headers=auth_header(self.viewer_token))
        assert res.status_code == 403
