from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"   # or "manager", "hr", "employee"


class UserRegister(BaseModel):
    """Schema for the /auth/create endpoint — creates a User account directly."""
    username: str
    password: str
    role: Optional[str] = "employee"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_name: Optional[str] = None

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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }