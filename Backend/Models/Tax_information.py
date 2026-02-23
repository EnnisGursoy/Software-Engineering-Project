from sqlalchemy import (
    Column, Integer, Date, DECIMAL, Enum, ForeignKey, Boolean, TIMESTAMP, String
)
from sqlalchemy.sql import func
from Backend.Database.connection import Base



class TaxInformation(Base):
    __tablename__ = "tax_information"

    tax_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)

    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)

    filing_status = Column(
        Enum("single", "married", "head_of_household", name="filing_status_enum"),
        nullable=False
    )

    federal_allowances = Column(Integer, nullable=False)
    state_allowances = Column(Integer, nullable=False)

    additional_withholding = Column(DECIMAL(8, 2), nullable=True)

    exempt_state = Column(Boolean, nullable=True)
    exempt_federal = Column(Boolean, nullable=True)

    effective_date = Column(Date, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<TaxInformation(id={self.tax_id}, employee_id={self.employee_id})>"
    