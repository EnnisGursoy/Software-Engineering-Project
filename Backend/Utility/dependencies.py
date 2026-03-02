from Backend.Database.connection import SessionLocal
from Backend.Utility.security import decode_access_token
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from Backend.Models import Employee
from fastapi.security import OAuth2PasswordBearer
from Backend.Models.User import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(Employee).filter(Employee.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def admin_only(admin : User = Depends(get_current_user)) -> User :
    if admin.role != "admin":
        raise HTTPException(status_code=400, detail = "Admin access required")
    
    return admin


def hr_only(hr : User = Depends(get_current_user)) -> User :
    if hr.role not in ["hr", "admin"] :
        raise HTTPException(status_code = 400, detail = "HR or Admin access is required")
    return hr
 
def manager_only(manager : User = Depends(get_current_user)) -> User :
    if manager.role not in ["manager", "admin", "hr"] :
        raise HTTPException(status_code = 400, details = "Manager or Admin or HR access is required")
    return manager
