from sqlalchemy import (
    Column, Integer, Date, DECIMAL, Enum, ForeignKey, Boolean, TIMESTAMP
)
from sqlalchemy.sql import func
from Backend.Database.connection import Base

class EmployeePosition(Base):
    __tablename__ = "employee_positions"

    emp_position_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.position_id"), nullable=False)

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    current_salary = Column(DECIMAL(10, 2), nullable=False)
    current_hourly_rate = Column(DECIMAL(8, 2), nullable=False)

    pay_frequency = Column(
        Enum("weekly", "bi_weekly", "semi_monthly", "monthly", name="pay_frequency_enum"),
        nullable=False
    )

    is_current = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return (
            f"<EmployeePosition(id={self.emp_position_id}, "
            f"employee_id={self.employee_id}, position_id={self.position_id})>"
        )