from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"   # or "manager", "hr", "employee"

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
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }