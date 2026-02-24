from sqlalchemy import Column, Integer, Date, Time, DECIMAL, Enum, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from Backend.Database.connection import Base

class TimeEntries(Base):
    __tablename__ = "time_entries"

    entry_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    clock_in = Column(Time, nullable=True)
    clock_out = Column(Time, nullable=True)

    regular_hours = Column(DECIMAL(5, 2), nullable=True)
    overtime_hours = Column(DECIMAL(5, 2), nullable=True)

    entry_type = Column(Enum("work", "sick", "vacation", "holiday", "unpaid"), nullable=True, default="work")
    notes = Column(Text, nullable=True)
    approved = Column(Boolean, nullable=True)
    approved_by = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)