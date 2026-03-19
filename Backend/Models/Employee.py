from sqlalchemy import Column, Integer, String, Date, Enum, TIMESTAMP, ForeignKey
from Backend.Database.connection import Base
from datetime import datetime
from sqlalchemy.orm import relationship
class Employee(Base):
    __tablename__ = "employees" 
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    employee_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    ssn = Column(String(225), nullable=False, unique=True)
    employment_status = Column(
        Enum("active", "terminated", "on_leave", name="employment_status_enum"),
        nullable=True,
        default="active"
    )
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)
    created_at = Column(Date, default=datetime.utcnow)
    updated_at = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="employee")

    def __repr__(self):
        return f"<Employee(employee_id={self.employee_id}, email='{self.email}')>"