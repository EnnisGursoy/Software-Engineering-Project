from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, Enum, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from Backend.Database.connection import Base


class BenefitEnrollment(Base):
    __tablename__ = "benefit_enrollments"

    enrollment_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id   = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    plan_id       = Column(Integer, ForeignKey("benefit_plans.plan_id"), nullable=False)
    status        = Column(Enum("Active", "Pending", "Inactive"), nullable=False, default="Active")
    start_date    = Column(Date, nullable=True)
    end_date      = Column(Date, nullable=True)
    employee_cost = Column(DECIMAL(8, 2), nullable=True)
    employer_cost = Column(DECIMAL(8, 2), nullable=True)
    notes         = Column(Text, nullable=True)
    created_at    = Column(TIMESTAMP, server_default=func.now())
