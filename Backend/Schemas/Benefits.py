from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date


class PlanCreate(BaseModel):
    plan_name:     str
    plan_type:     str
    provider:      Optional[str]   = None
    employee_cost: Optional[float] = 0.0
    employer_cost: Optional[float] = 0.0
    coverage_level: Optional[str]  = None
    notes:         Optional[str]   = None


class PlanOut(BaseModel):
    plan_id:       int
    plan_name:     str
    plan_type:     str
    provider:      Optional[str]
    employee_cost: Optional[float]
    employer_cost: Optional[float]
    coverage_level: Optional[str]
    notes:         Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PlanUpdate(BaseModel):
    plan_name:     Optional[str]   = None
    plan_type:     Optional[str]   = None
    provider:      Optional[str]   = None
    employee_cost: Optional[float] = None
    employer_cost: Optional[float] = None
    coverage_level: Optional[str]  = None
    notes:         Optional[str]   = None


class EnrollmentCreate(BaseModel):
    employee_id:   int
    plan_id:       int
    status:        Optional[str]   = "Active"
    start_date:    Optional[date]  = None
    end_date:      Optional[date]  = None
    employee_cost: Optional[float] = None
    employer_cost: Optional[float] = None
    notes:         Optional[str]   = None


class EnrollmentOut(BaseModel):
    enrollment_id: int
    employee_id:   int
    plan_id:       int
    status:        str
    start_date:    Optional[date]
    end_date:      Optional[date]
    employee_cost: Optional[float]
    employer_cost: Optional[float]
    notes:         Optional[str]

    model_config = ConfigDict(from_attributes=True)


class EnrollmentUpdate(BaseModel):
    status:        Optional[str]   = None
    start_date:    Optional[date]  = None
    end_date:      Optional[date]  = None
    employee_cost: Optional[float] = None
    employer_cost: Optional[float] = None
    notes:         Optional[str]   = None
