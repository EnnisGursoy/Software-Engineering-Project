from sqlalchemy import Column, Integer, String, DECIMAL, Text, TIMESTAMP, Enum
from sqlalchemy.sql import func
from Backend.Database.connection import Base


class BenefitPlan(Base):
    __tablename__ = "benefit_plans"

    plan_id       = Column(Integer, primary_key=True, autoincrement=True)
    plan_name     = Column(String(100), nullable=False)
    plan_type     = Column(Enum("Health", "Dental", "Vision", "Life", "Retirement", "Other"), nullable=False)
    provider      = Column(String(100), nullable=True)
    employee_cost = Column(DECIMAL(8, 2), nullable=True, default=0)
    employer_cost = Column(DECIMAL(8, 2), nullable=True, default=0)
    coverage_level = Column(String(50), nullable=True)
    notes         = Column(Text, nullable=True)
    created_at    = Column(TIMESTAMP, server_default=func.now())
