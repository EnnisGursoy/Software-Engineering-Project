from sqlalchemy import Column, Integer, String, Enum, Date, TIMESTAMP, Float, ForeignKey
from sqlalchemy.sql import func
from Backend.Database.connection import Base

class Paychecks(Base):
    __tablename__ = "paychecks"

    paycheck_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    pay_period_id = Column(Integer, ForeignKey("pay_periods.pay_period_id"), nullable=False)
    check_number = Column(String(50), nullable=True)

    gross_pay = Column(Float, nullable=False)
    net_pay = Column(Float, nullable=False)

    federal_tax = Column(Float, nullable=True)
    state_tax = Column(Float, nullable=True)
    social_security = Column(Float, nullable=True)
    medicare = Column(Float, nullable=True)
    health_insurance = Column(Float, nullable=True)
    retirement_401k = Column(Float, nullable=True)
    other_deductions = Column(Float, nullable=True)

    payment_method = Column(Enum("direct deposit", "check", "cash"), nullable=True, default="direct deposit")
    payment_status = Column(Enum("pending", "processed", "paid", "void"), nullable=True, default="pending")
    payment_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)