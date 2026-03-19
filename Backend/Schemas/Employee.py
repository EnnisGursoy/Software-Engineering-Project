from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional
from Backend.Schemas.User import UserCreate, UserOut



class EmployeeCreate(BaseModel):
    user : UserCreate
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
    ssn: str                                  
    employment_status: Optional[str] = "active"
    department_name: Optional[str] = None


class EmployeeOut(BaseModel):
    user : UserOut
    employee_id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    department_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)



class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    department_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

