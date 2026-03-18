from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from Backend.Database.connection import Base


class LoginLog(Base):
    __tablename__ = "login_logs"

    log_id       = Column(Integer, primary_key=True, autoincrement=True)
    username     = Column(String(150), nullable=False)
    ip_address   = Column(String(45), nullable=True)
    success      = Column(Boolean, nullable=False, default=False)
    attempted_at = Column(TIMESTAMP, server_default=func.now())
