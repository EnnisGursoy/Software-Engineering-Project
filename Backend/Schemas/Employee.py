from pydantic import BaseModel
from datetime import date

class Employee(BaseModel):
    id: int
    name: str
    position: str
    department: str
    date_joined: date

    class Config:
        orm_mode = True

class EmployeeCreate(BaseModel):
    name: str
    position: str
    department: str
    date_joined: date
    class Config:
        orm_mode = True

class EmployeeUpdate(BaseModel):
    name: str
    position: str
    department: str
    class Config:
        orm_mode = True

