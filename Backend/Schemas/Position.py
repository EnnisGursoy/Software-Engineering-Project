from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class PositionCreate(BaseModel):
    position_title: str
    department_id: Optional[int] = None
    base_salary: Optional[float] = 0.0
    hourly_rate: Optional[float] = 0.0
    employment_type: str  # full_time, part_time, contract


class PositionOut(BaseModel):
    position_id: int
    position_title: Optional[str]
    department_id: Optional[int]
    base_salary: Optional[float]
    hourly_rate: Optional[float]
    employment_type: str

    model_config = ConfigDict(from_attributes=True)


class PositionUpdate(BaseModel):
    position_title: Optional[str] = None
    department_id: Optional[int] = None
    base_salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    employment_type: Optional[str] = None


class EmployeePositionCreate(BaseModel):
    employee_id: int
    position_id: int
    start_date: Optional[date] = None
    current_salary: float = 0.0
    current_hourly_rate: float = 0.0
    pay_frequency: str  # weekly, bi_weekly, semi_monthly, monthly


class EmployeePositionOut(BaseModel):
    emp_position_id: int
    employee_id: int
    position_id: int
    start_date: Optional[date]
    end_date: Optional[date]
    current_salary: float
    current_hourly_rate: float
    pay_frequency: str
    is_current: bool

    model_config = ConfigDict(from_attributes=True)
