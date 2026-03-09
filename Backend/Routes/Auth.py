from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from Backend.Utility.dependencies import get_db, admin_only
from Backend.Models.User import User
from Backend.Schemas.User import UserCreate, UserOut
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
        "role": user.role
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

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user