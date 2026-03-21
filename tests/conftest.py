"""
Shared pytest configuration and fixtures for the Pay Central API test suite.

IMPORTANT: Environment variables MUST be set before any Backend module is
imported, because security.py reads ENCRYPTION_KEY and SECRET_KEY at module
load time via os.getenv / decouple.config.
"""
import os
from cryptography.fernet import Fernet

# ── Set all required env vars BEFORE importing anything from Backend ───────────
_TEST_FERNET_KEY = Fernet.generate_key().decode()

os.environ["SECRET_KEY"] = "test-secret-key-pay-central-api-do-not-use-in-prod"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["ENCRYPTION_KEY"] = _TEST_FERNET_KEY
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# ───────────────────────────────────────────────────────────────────────────────

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from Backend.Database.connection import Base
from Backend.main import app
from Backend.Utility.dependencies import get_db
from Backend.Utility.security import hash_password, create_access_token, encrypt_ssn
from Backend.Models.User import User
from Backend.Models.Employee import Employee
from Backend.Models.department import Department


def _make_test_engine():
    """
    Create a fresh in-memory SQLite engine.

    StaticPool forces all connections to share the SAME in-memory database.
    Without it, each new connection from the pool gets a blank :memory: DB,
    so tables created by create_all() are invisible to the session.
    """
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="function")
def db():
    """
    Provide a fully isolated SQLite in-memory session for each test.
    Tables are created before the test and dropped after, ensuring zero
    state leaks between tests.
    """
    engine = _make_test_engine()
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Override FastAPI's get_db so TestClient uses the same session
    def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def client(db):
    """TestClient wired to the isolated test database."""
    with TestClient(app) as c:
        yield c


# ── User fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db) -> User:
    user = User(
        username="test_admin",
        password_hash=hash_password("Admin@1234"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def hr_user(db) -> User:
    user = User(
        username="test_hr",
        password_hash=hash_password("Hr@1234"),
        role="hr",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def manager_user(db) -> User:
    user = User(
        username="test_manager",
        password_hash=hash_password("Manager@1234"),
        role="manager",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Auth token helpers ─────────────────────────────────────────────────────────

def make_token(user: User) -> str:
    return create_access_token({
        "sub": str(user.user_id),
        "role": user.role,
        "username": user.username,
    })


def auth_headers(user: User) -> dict:
    return {"Authorization": f"Bearer {make_token(user)}"}


@pytest.fixture
def admin_headers(admin_user) -> dict:
    return auth_headers(admin_user)


@pytest.fixture
def hr_headers(hr_user) -> dict:
    return auth_headers(hr_user)


@pytest.fixture
def manager_headers(manager_user) -> dict:
    return auth_headers(manager_user)


# ── Domain object fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def sample_employee(db) -> Employee:
    emp = Employee(
        first_name="Jane",
        last_name="Testsmith",
        email="jane.testsmith@example.com",
        hire_date=date(2022, 6, 1),
        ssn=encrypt_ssn("234-56-7891"),
        employment_status="active",
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@pytest.fixture
def sample_department(db) -> Department:
    dept = Department(department_name="Engineering", manager_id=None)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
