from sqlalchemy import Column, Integer, Date, Enum, TIMESTAMP
from sqlalchemy.sql import func
from Backend.Database.connection import Base

class PayPeriods(Base):
    __tablename__ = "pay_periods"

    pay_period_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    period_start_date = Column(Date, nullable=False)
    period_end_date = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=False)
    period_type = Column(Enum("weekly", "bi_weekly", "semi_monthly", "monthly"), nullable=False)
    status = Column(Enum("open", "processing", "paid", "closed"), nullable=True, default="open")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)