from pydantic import BaseModel, ConfigDict, model_validator
from datetime import date
from typing import Optional
from enum import Enum


class PeriodType(str, Enum):
    weekly = "weekly"
    bi_weekly = "bi_weekly"
    semi_monthly = "semi_monthly"
    monthly = "monthly"


class PeriodStatus(str, Enum):
    open = "open"
    processing = "processing"
    paid = "paid"
    closed = "closed"


class PayPeriodCreate(BaseModel):
    period_start_date: date
    period_end_date: date
    pay_date: date
    period_type: PeriodType
    status: Optional[PeriodStatus] = PeriodStatus.open

    @model_validator(mode="after")
    def end_after_start(self):
        if self.period_end_date < self.period_start_date:
            raise ValueError("period_end_date must be on or after period_start_date")
        return self

    model_config = ConfigDict(from_attributes=True)


class PayPeriodUpdate(BaseModel):
    period_start_date: Optional[date] = None
    period_end_date: Optional[date] = None
    pay_date: Optional[date] = None
    period_type: Optional[PeriodType] = None
    status: Optional[PeriodStatus] = None

    model_config = ConfigDict(from_attributes=True)


class PayPeriodOut(BaseModel):
    pay_period_id: int
    period_start_date: date
    period_end_date: date
    pay_date: date
    period_type: PeriodType
    status: Optional[PeriodStatus]

    model_config = ConfigDict(from_attributes=True)

class PayPeriodStatusUpdate(BaseModel):
    status: PeriodStatus

    model_config = ConfigDict(from_attributes=True)
