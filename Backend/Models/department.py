from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from Backend.Database.connection import Base

class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    department_name = Column(String(100), nullable=False)

    # manager_id references employees table (nullable)
    manager_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)

    # manager_user_id: stores the user_id of the manager directly (for managers without employee records)
    manager_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Department(id={self.department_id}, name='{self.department_name}')>"