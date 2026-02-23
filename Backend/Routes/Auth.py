from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from Backend.Utility.dependencies import get_db
from Backend.Models.User import User
from Backend.Schemas.User import UserCreate, UserOut
from Backend.Utility.security import hash_password

router = APIRouter()


@router.post("/create", response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash password
    hashed_password = hash_password(user.password)

    # Create new user
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