from pydantic import BaseModel
from datetime import date
from typing import Optional


class PaycheckCreate(BaseModel):
    employee_id: int
    pay_period_id: int
    check_number: Optional[str] = None
    gross_pay: float
    net_pay: float
    federal_tax: Optional[float] = 0.0
    state_tax: Optional[float] = 0.0
    social_security: Optional[float] = 0.0
    medicare: Optional[float] = 0.0
    health_insurance: Optional[float] = 0.0
    retirement_401k: Optional[float] = 0.0
    other_deductions: Optional[float] = 0.0
    payment_method: Optional[str] = "direct deposit"
    payment_status: Optional[str] = "pending"
    payment_date: Optional[date] = None


class PaycheckOut(BaseModel):
    paycheck_id: int
    employee_id: int
    pay_period_id: int
    check_number: Optional[str]
    gross_pay: float
    net_pay: float
    federal_tax: Optional[float]
    state_tax: Optional[float]
    social_security: Optional[float]
    medicare: Optional[float]
    health_insurance: Optional[float]
    retirement_401k: Optional[float]
    other_deductions: Optional[float]
    payment_method: Optional[str]
    payment_status: Optional[str]
    payment_date: Optional[date]

    class Config:
        orm_mode = True


class PaycheckStatusUpdate(BaseModel):
    payment_status: str
    payment_date: Optional[date] = None
