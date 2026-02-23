from sqlalchemy import (
    Column, Integer, Date, DECIMAL, Enum, ForeignKey, Boolean, TIMESTAMP, String
)
from sqlalchemy.sql import func
from Backend.Database.connection import Base


class Positions(Base):
    __tablename__ = "positions"

    position_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    position_title = Column(String(100), nullable=True)

    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)

    base_salary = Column(DECIMAL(10, 2), nullable=True)
    hourly_rate = Column(DECIMAL(8, 2), nullable=True)

    employment_type = Column(
        Enum("full_time", "part_time", "contract", name="employment_type_enum"),
        nullable=False
    )

    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Position(id={self.position_id}, title='{self.position_title}')>"