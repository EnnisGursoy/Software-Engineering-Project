from Backend.Database.connection import Base
from sqlalchemy import Column, Integer, String

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"