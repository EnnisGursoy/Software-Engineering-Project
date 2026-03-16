from pydantic import BaseModel
from datetime import date
from typing import Optional


class TaxInfoCreate(BaseModel):
    employee_id: int
    filing_status: str  # single, married, head_of_household
    federal_allowances: int = 0
    state_allowances: int = 0
    additional_withholding: Optional[float] = 0.0
    exempt_state: Optional[bool] = False
    exempt_federal: Optional[bool] = False
    effective_date: Optional[date] = None


class TaxInfoOut(BaseModel):
    tax_id: int
    employee_id: int
    filing_status: str
    federal_allowances: int
    state_allowances: int
    additional_withholding: Optional[float]
    exempt_state: Optional[bool]
    exempt_federal: Optional[bool]
    effective_date: Optional[date]

    class Config:
        orm_mode = True


class TaxInfoUpdate(BaseModel):
    filing_status: Optional[str] = None
    federal_allowances: Optional[int] = None
    state_allowances: Optional[int] = None
    additional_withholding: Optional[float] = None
    exempt_state: Optional[bool] = None
    exempt_federal: Optional[bool] = None
    effective_date: Optional[date] = None
