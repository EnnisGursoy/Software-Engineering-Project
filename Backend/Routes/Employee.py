from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only
from Backend.Models.Employee import Employee, User
from Backend.Schemas.Employee import EmployeeCreate, EmployeeOut
from Backend.Services.employee_service import create_employee

router = APIRouter()


@router.post('/sign_up', response_model = EmployeeOut)
async def register(employee:EmployeeCreate,  user : User = Depends(hr_only), db : Session = Depends(get_db)) :
   new_employee =  create_employee(employee, db)
   return new_employee



    