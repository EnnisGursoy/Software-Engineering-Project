from pydantic import BaseModel
from datetime import date
from typing import Optional


class PayPeriodCreate(BaseModel):
    period_start_date: date
    period_end_date: date
    pay_date: date
    period_type: str  # weekly, bi_weekly, semi_monthly, monthly


class PayPeriodOut(BaseModel):
    pay_period_id: int
    period_start_date: date
    period_end_date: date
    pay_date: date
    period_type: str
    status: Optional[str]

    class Config:
        orm_mode = True


class PayPeriodStatusUpdate(BaseModel):
    status: str  # open, processing, paid, closed
