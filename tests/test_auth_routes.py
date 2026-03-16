"""
Integration tests for the /auth routes.

Uses FastAPI TestClient with an in-memory SQLite database (injected via
the `client` fixture from conftest.py).  Each test gets a fresh database
so there are no ordering dependencies between tests.
"""
import pytest
from tests.conftest import auth_headers


# ── POST /auth/create ──────────────────────────────────────────────────────────

class TestCreateUser:
    def test_first_user_is_promoted_to_admin(self, client):
        """When the DB is empty the first user always becomes admin."""
        resp = client.post("/auth/create", json={
            "username": "firstuser",
            "password": "Password123",
            "first_name": "First",
            "last_name": "User",
            "role": "hr",          # will be overridden to "admin"
        })
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_second_user_requires_admin_auth(self, client, admin_user, admin_headers):
        """After the first user exists, only an admin can create more users."""
        resp = client.post("/auth/create", json={
            "username": "seconduser",
            "password": "Password123",
            "role": "hr",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "seconduser"

    def test_duplicate_username_returns_400(self, client, admin_user, admin_headers):
        client.post("/auth/create", json={
            "username": "dupuser",
            "password": "Password123",
            "role": "hr",
        }, headers=admin_headers)
        resp = client.post("/auth/create", json={
            "username": "dupuser",
            "password": "Password456",
            "role": "manager",
        }, headers=admin_headers)
        assert resp.status_code == 400

    def test_non_admin_cannot_create_user(self, client, hr_user, hr_headers):
        resp = client.post("/auth/create", json={
            "username": "tryinguser",
            "password": "Password123",
            "role": "hr",
        }, headers=hr_headers)
        assert resp.status_code == 403

    def test_create_with_invalid_department_returns_404(self, client, admin_user, admin_headers):
        resp = client.post("/auth/create", json={
            "username": "nodeptuser",
            "password": "Password123",
            "role": "hr",
            "department_name": "Ghost Department",
        }, headers=admin_headers)
        assert resp.status_code == 404


# ── POST /auth/login ───────────────────────────────────────────────────────────

class TestLogin:
    def test_valid_credentials_return_token(self, client, admin_user):
        resp = client.post("/auth/login", data={
            "username": "test_admin",
            "password": "Admin@1234",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client, admin_user):
        resp = client.post("/auth/login", data={
            "username": "test_admin",
            "password": "WrongPassword",
        })
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(self, client):
        resp = client.post("/auth/login", data={
            "username": "nobody",
            "password": "anything",
        })
        assert resp.status_code == 401

    def test_token_is_usable_for_protected_routes(self, client, admin_user):
        login_resp = client.post("/auth/login", data={
            "username": "test_admin",
            "password": "Admin@1234",
        })
        token = login_resp.json()["access_token"]
        me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "test_admin"


# ── GET /auth/me ───────────────────────────────────────────────────────────────

class TestGetMe:
    def test_returns_current_user_profile(self, client, admin_user, admin_headers):
        resp = client.get("/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "test_admin"
        assert data["role"] == "admin"

    def test_includes_expected_fields(self, client, admin_user, admin_headers):
        resp = client.get("/auth/me", headers=admin_headers)
        body = resp.json()
        for field in ("user_id", "username", "role", "is_active"):
            assert field in body

    def test_hr_user_returns_hr_role(self, client, hr_user, hr_headers):
        resp = client.get("/auth/me", headers=hr_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "hr"


# ── PATCH /auth/me ─────────────────────────────────────────────────────────────

class TestUpdateProfile:
    def test_update_first_name(self, client, admin_user, admin_headers):
        resp = client.patch("/auth/me", json={"first_name": "Updated"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Updated"

    def test_update_last_name(self, client, admin_user, admin_headers):
        resp = client.patch("/auth/me", json={"last_name": "Newlast"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["last_name"] == "Newlast"

    def test_update_persists_to_get_me(self, client, admin_user, admin_headers):
        client.patch("/auth/me", json={"first_name": "Persistent"}, headers=admin_headers)
        resp = client.get("/auth/me", headers=admin_headers)
        assert resp.json()["first_name"] == "Persistent"


# ── POST /auth/change-password ─────────────────────────────────────────────────

class TestChangePassword:
    def test_correct_current_password_succeeds(self, client, admin_user, admin_headers):
        resp = client.post("/auth/change-password", json={
            "current_password": "Admin@1234",
            "new_password": "NewAdmin@5678",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert "updated" in resp.json()["detail"].lower()

    def test_new_password_is_active(self, client, admin_user, admin_headers):
        client.post("/auth/change-password", json={
            "current_password": "Admin@1234",
            "new_password": "BrandNew@999",
        }, headers=admin_headers)
        # Old password should no longer work
        resp = client.post("/auth/login", data={
            "username": "test_admin",
            "password": "Admin@1234",
        })
        assert resp.status_code == 401

    def test_wrong_current_password_returns_400(self, client, admin_user, admin_headers):
        resp = client.post("/auth/change-password", json={
            "current_password": "WrongCurrent",
            "new_password": "NewPass@1234",
        }, headers=admin_headers)
        assert resp.status_code == 400


# ── DELETE /auth/{user_id} ─────────────────────────────────────────────────────

class TestDeleteUser:
    def test_admin_can_delete_other_user(self, client, admin_user, admin_headers, hr_user):
        resp = client.delete(f"/auth/{hr_user.user_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    def test_admin_cannot_delete_own_account(self, client, admin_user, admin_headers):
        resp = client.delete(f"/auth/{admin_user.user_id}", headers=admin_headers)
        assert resp.status_code == 400

    def test_delete_nonexistent_user_returns_404(self, client, admin_user, admin_headers):
        resp = client.delete("/auth/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_non_admin_cannot_delete_user(self, client, hr_user, hr_headers, manager_user):
        resp = client.delete(f"/auth/{manager_user.user_id}", headers=hr_headers)
        assert resp.status_code == 403
