from pydantic import BaseModel, ConfigDict
from datetime import date, time
from typing import Optional


class TimeEntryCreate(BaseModel):
    employee_id: int
    entry_date: date
    clock_in: Optional[time] = None
    clock_out: Optional[time] = None
    regular_hours: Optional[float] = None
    overtime_hours: Optional[float] = 0.0
    entry_type: Optional[str] = "work"
    notes: Optional[str] = None


class TimeEntryOut(BaseModel):
    entry_id: int
    employee_id: int
    entry_date: date
    clock_in: Optional[time]
    clock_out: Optional[time]
    regular_hours: Optional[float]
    overtime_hours: Optional[float]
    entry_type: Optional[str]
    notes: Optional[str]
    approved: Optional[bool]
    approved_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class TimeEntryApprove(BaseModel):
    approved: bool

class TimeEntryUpdate(BaseModel):
    clock_in: Optional[time] = None
    clock_out: Optional[time] = None
    regular_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    entry_type: Optional[str] = None
    notes: Optional[str] = None
