from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from Backend.Utility.dependencies import get_db, admin_only, get_current_user
from Backend.Models.User import User
from Backend.Models.Department import Department
from Backend.Models.LoginLog import LoginLog
from Backend.Schemas.User import UserCreate, UserOut, UserRegister, ChangePassword, UpdateProfile
from Backend.Utility.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str


class ResetPassword(BaseModel):
    username: str
    new_password: str



router = APIRouter()


def authenticate(username: str, password: str, db: Session):
    # Find user by username
    existing_user = db.query(User).filter(User.username == username).first()

    if not existing_user:
       return None
    # Verify password
    if not verify_password(password, existing_user.password_hash):
       return None

    return existing_user


@router.get("/setup-status")
async def setup_status(db: Session = Depends(get_db)):
    return {"needs_setup": db.query(User).count() == 0}


@router.post("/login", response_model=Token)
async def auth_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate(
        username=form_data.username,
        password=form_data.password,
        db=db
    )

    ip = request.client.host if request.client else None
    db.add(LoginLog(username=form_data.username, ip_address=ip, success=user is not None))
    db.commit()

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token_data = {
        "sub": str(user.user_id),
        "role": user.role,
        "username": user.username,
    }

    access_token = create_access_token(token_data)

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/create", response_model=UserOut)
async def register_user(
    body: UserRegister,
    db: Session = Depends(get_db),
    _ = Depends(admin_only)
):
    # Resolve department if provided
    department_id = None
    if body.department_name:
        dept = db.query(Department).filter(
            Department.department_name == body.department_name
        ).first()
        if not dept:
            raise HTTPException(
                status_code=404,
                detail=f"Department '{body.department_name}' not found"
            )
        department_id = dept.department_id

    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # First user ever is always promoted to admin
    if db.query(User).count() == 0:
        body.role = "admin"

    new_user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
        first_name=body.first_name,
        last_name=body.last_name,
        department_id=department_id,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if body.first_name is not None:
        current_user.first_name = body.first_name
    if body.last_name is not None:
        current_user.last_name = body.last_name
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    db.delete(user)
    db.commit()
    return {"message": "User permanently deleted"}


@router.post("/change-password")
async def change_password(
    body: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(body.new_password)
    db.commit()

    return {"detail": "Password updated successfully"}


@router.post("/reset-password")
async def admin_reset_password(
    body: ResetPassword,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    user = db.query(User).filter(User.username == body.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"detail": f"Password reset for '{body.username}'"}


@router.get("/logs")
async def get_login_logs(
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    logs = db.query(LoginLog).order_by(LoginLog.attempted_at.desc()).limit(200).all()
    return [
        {
            "log_id":      l.log_id,
            "username":    l.username,
            "ip_address":  l.ip_address,
            "success":     l.success,
            "attempted_at": str(l.attempted_at),
        }
        for l in logs
    ]