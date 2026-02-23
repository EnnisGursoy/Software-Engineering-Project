from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional



class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    date_of_birth: Optional[date] = None
    hire_date: date
    ssn: Optional[str] = None
    employment_status: str = "active"