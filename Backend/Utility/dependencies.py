from Backend.Database.connection import SessionLocal
from Backend.Utility.security import decode_access_token
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from Backend.Models.User import User
from Backend.Models.Employee import Employee

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=False
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User | None:
    """Returns the current user or None if no token is provided."""
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_current_user(
    user: User | None = Depends(get_optional_user),
) -> User:
    """Returns the current authenticated user, raising 401 if not authenticated."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ---------------------------------------------------------
# Admin dependency with first-user bootstrap
# ---------------------------------------------------------
def get_current_employee(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Employee:
    """Returns the Employee record linked to the logged-in user."""
    emp = db.query(Employee).filter(Employee.user_id == current_user.user_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="No employee record linked to this account")
    return emp


def admin_only(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user)
):
    total_users = db.query(User).count()

    # Allow first user creation without login
    if total_users == 0:
        return None

    # After first user exists → must be admin
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return current_user


# ---------------------------------------------------------
# HR dependency
# ---------------------------------------------------------
def hr_only(current_user: User = Depends(get_current_user)) -> User:
    if not current_user or current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=403, detail="HR or Admin access required")
    return current_user


# ---------------------------------------------------------
# Manager dependency
# ---------------------------------------------------------
def manager_only(current_user: User = Depends(get_current_user)) -> User:
    if not current_user or current_user.role not in ["manager", "admin", "hr"]:
        raise HTTPException(status_code=403, detail="Manager, Admin, or HR access required")
    return current_user


# ---------------------------------------------------------
# Admin or Manager dependency
# ---------------------------------------------------------
def admin_or_manager(current_user: User = Depends(get_current_user)) -> User:
    if not current_user or current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")
    return current_user