from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

class TaxCreate(BaseModel):
    employee_id: int
    filing_status: str
    federal_allowances: int
    state_allowances: int
    additional_withholding: Optional[float] = None
    exempt_state: Optional[bool] = None
    exempt_federal: Optional[bool] = None
    effective_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class TaxUpdate(BaseModel):
    filing_status: Optional[str] = None
    federal_allowances: Optional[int] = None
    state_allowances: Optional[int] = None
    additional_withholding: Optional[float] = None
    exempt_state: Optional[bool] = None
    exempt_federal: Optional[bool] = None
    effective_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class TaxOut(BaseModel):
    tax_id: int
    employee_id: int
    filing_status: str
    federal_allowances: int
    state_allowances: int
    additional_withholding: Optional[float]
    exempt_state: Optional[bool]
    exempt_federal: Optional[bool]
    effective_date: Optional[date]

    model_config = ConfigDict(from_attributes=True)