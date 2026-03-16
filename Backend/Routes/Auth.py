from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from Backend.Utility.dependencies import get_db, admin_only, get_current_user
from Backend.Models.User import User
from Backend.Models.Department import Department
from Backend.Schemas.User import UserCreate, UserOut, ChangePassword, UpdateProfile
from Backend.Utility.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str



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


@router.post("/login", response_model=Token)
async def auth_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate(
        username=form_data.username,
        password=form_data.password,
        db=db
    )

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token_data = {
        "sub": str(user.user_id),
        "role": user.role,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

    access_token = create_access_token(token_data)

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/create", response_model=UserOut)
async def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    _ = Depends(admin_only)
):
    total_users = db.query(User).count()

    # First user becomes admin
    if total_users == 0:
        user.role = "admin"

    # Check duplicate username
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Look up department by name if provided
    department_id = None
    if user.department_name:
        dept = db.query(Department).filter(Department.department_name == user.department_name).first()
        if not dept:
            raise HTTPException(status_code=404, detail=f"Department '{user.department_name}' not found")
        department_id = dept.department_id

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        department_id=department_id,
        is_active=True
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