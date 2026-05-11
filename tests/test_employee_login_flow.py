"""
End-to-end tests for the FR-2 fix: when an admin/HR adds an Employee, a
login is auto-provisioned (username = email + temp password) and the
employee can sign in with their email.

Covers:
  * /employee/sign_up auto-creates a User row and returns the temp password
  * /auth/login accepts EITHER the original username OR the work email
  * The temp password actually works as the employee's first password
  * Existing admin/HR/manager logins (by username) still work — no regression
"""


class TestEmployeeAutoLogin:
    """`POST /employee/sign_up` should provision a working login."""

    def _payload(self, **overrides):
        body = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "ssn": "234-56-7890",
            "hire_date": "2026-01-01",
            "employment_status": "active",
        }
        body.update(overrides)
        return body

    def test_response_contains_temp_password_and_login_username(
        self, client, admin_user, admin_headers
    ):
        resp = client.post("/employee/sign_up", json=self._payload(), headers=admin_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["login_username"] == "jane.doe@example.com"
        assert isinstance(data["temp_password"], str)
        assert len(data["temp_password"]) >= 8

    def test_employee_can_login_with_email_and_temp_password(
        self, client, admin_user, admin_headers
    ):
        resp = client.post("/employee/sign_up", json=self._payload(), headers=admin_headers)
        creds = resp.json()

        login = client.post(
            "/auth/login",
            data={"username": creds["login_username"], "password": creds["temp_password"]},
        )
        assert login.status_code == 200, login.text
        assert "access_token" in login.json()

    def test_logged_in_employee_can_load_their_profile(
        self, client, admin_user, admin_headers
    ):
        creds = client.post(
            "/employee/sign_up", json=self._payload(), headers=admin_headers
        ).json()
        token = client.post(
            "/auth/login",
            data={"username": creds["login_username"], "password": creds["temp_password"]},
        ).json()["access_token"]

        me = client.get("/employee/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "jane.doe@example.com"

    def test_email_collision_with_existing_username_skips_user_creation(
        self, client, admin_user, admin_headers, db
    ):
        # Pre-create a User whose username is the email we're about to assign
        from Backend.Models.User import User
        from Backend.Utility.security import hash_password
        db.add(User(
            username="jane.doe@example.com",
            password_hash=hash_password("doesnt-matter"),
            role="hr",
            is_active=True,
        ))
        db.commit()

        resp = client.post("/employee/sign_up", json=self._payload(), headers=admin_headers)
        assert resp.status_code == 200, resp.text
        # Employee saved, but no new login was provisioned
        assert resp.json()["temp_password"] is None
        assert resp.json()["login_username"] is None


class TestGenerateLoginForExistingEmployee:
    """`POST /employee/{id}/generate-login` provisions a login for an
    employee that pre-dates the FR-2 fix (no `user_id` link)."""

    def _orphan_employee(self, db, email="legacy@example.com", ssn="234-56-7895"):
        from datetime import date
        from Backend.Models.Employee import Employee
        from Backend.Utility.security import encrypt_ssn
        emp = Employee(
            first_name="Legacy",
            last_name="Hire",
            email=email,
            ssn=encrypt_ssn(ssn),
            hire_date=date(2024, 1, 1),
            employment_status="active",
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
        return emp

    def test_returns_temp_password_and_links_user(self, client, db, admin_user, admin_headers):
        emp = self._orphan_employee(db)
        resp = client.post(f"/employee/{emp.employee_id}/generate-login", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["login_username"] == "legacy@example.com"
        assert isinstance(data["temp_password"], str) and len(data["temp_password"]) >= 8

        db.refresh(emp)
        assert emp.user_id is not None

    def test_generated_credentials_actually_log_in(self, client, db, admin_user, admin_headers):
        emp = self._orphan_employee(db, email="works@example.com", ssn="234-56-7896")
        creds = client.post(
            f"/employee/{emp.employee_id}/generate-login", headers=admin_headers
        ).json()
        login = client.post(
            "/auth/login",
            data={"username": creds["login_username"], "password": creds["temp_password"]},
        )
        assert login.status_code == 200

    def test_already_linked_employee_returns_400(self, client, db, admin_user, admin_headers):
        # Create with the auto-provisioning path so user_id is already set
        client.post("/employee/sign_up", json={
            "first_name": "Already", "last_name": "Linked",
            "email": "linked@example.com", "ssn": "234-56-7897",
            "hire_date": "2026-01-01", "employment_status": "active",
        }, headers=admin_headers)
        from Backend.Models.Employee import Employee
        emp = db.query(Employee).filter_by(email="linked@example.com").first()
        resp = client.post(f"/employee/{emp.employee_id}/generate-login", headers=admin_headers)
        assert resp.status_code == 400

    def test_username_collision_returns_409(self, client, db, admin_user, admin_headers):
        from Backend.Models.User import User
        from Backend.Utility.security import hash_password
        # Plant a User whose username collides with the email we're about to generate for
        db.add(User(
            username="taken@example.com",
            password_hash=hash_password("x"),
            role="hr",
            is_active=True,
        ))
        db.commit()

        emp = self._orphan_employee(db, email="taken@example.com", ssn="234-56-7898")
        resp = client.post(f"/employee/{emp.employee_id}/generate-login", headers=admin_headers)
        assert resp.status_code == 409


class TestLoginByEmailOrUsername:
    """`POST /auth/login` should accept either form."""

    def test_login_by_username_still_works(self, client, admin_user):
        resp = client.post(
            "/auth/login",
            data={"username": "test_admin", "password": "Admin@1234"},
        )
        assert resp.status_code == 200

    def test_login_by_email_works_when_user_linked_to_employee(
        self, client, admin_user, admin_headers
    ):
        creds = client.post(
            "/employee/sign_up",
            json={
                "first_name": "Mark",
                "last_name": "Twain",
                "email": "mark.twain@example.com",
                "ssn": "234-56-7891",
                "hire_date": "2026-01-01",
                "employment_status": "active",
            },
            headers=admin_headers,
        ).json()

        # Logging in with the email should hit the email-fallback path
        resp = client.post(
            "/auth/login",
            data={"username": "mark.twain@example.com", "password": creds["temp_password"]},
        )
        assert resp.status_code == 200

    def test_unknown_email_returns_401_not_500(self, client):
        resp = client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "whatever"},
        )
        assert resp.status_code == 401

    def test_known_email_wrong_password_returns_401(
        self, client, admin_user, admin_headers
    ):
        client.post(
            "/employee/sign_up",
            json={
                "first_name": "Wrong",
                "last_name": "Password",
                "email": "wp@example.com",
                "ssn": "234-56-7892",
                "hire_date": "2026-01-01",
                "employment_status": "active",
            },
            headers=admin_headers,
        )
        resp = client.post(
            "/auth/login",
            data={"username": "wp@example.com", "password": "definitely-wrong"},
        )
        assert resp.status_code == 401
