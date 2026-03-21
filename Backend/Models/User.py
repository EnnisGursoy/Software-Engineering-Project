from sqlalchemy import Column, Integer, String, Date, Enum, TIMESTAMP, Boolean, ForeignKey
from Backend.Database.connection import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("admin", "manager", "hr","employee",  name="user_roles"), default="employee") #hr = human responsibility role
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)
    is_active = Column(Boolean, default=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    employee = relationship("Employee", back_populates="user", uselist=False)


    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', role='{self.role}')>"