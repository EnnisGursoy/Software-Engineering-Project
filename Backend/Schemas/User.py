from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"   # or "manager", "hr", "employee"


class UserRegister(BaseModel):
    """Flat schema for POST /auth/create — creates a user account only."""
    username: str
    password: str
    role: str = "employee"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_name: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class UserLogin(BaseModel):
    username: str
    password: str


class UpdateProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    user_id: int
    username: str
    role: str
    is_active: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)