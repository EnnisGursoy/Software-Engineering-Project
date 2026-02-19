from sqlalchemy import Column, Integer, String
from Backend.Database.connection import Base

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    position = Column(String(100), index=True)
    department = Column(String(100), index=True)
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', position='{self.position}', department='{self.department}')>"
    
    