from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, admin_only, manager_only
from Backend.Models.User import User
from Backend.Schemas.Employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from Backend.Services.employee_service import create_employee, update_employee, show_employee, show_all_employees, delete_employee, hard_delete_employee, get_employees_by_department

router = APIRouter()

@router.get('/by-department/{department_id}')
async def get_by_department(department_id: int, user: User = Depends(manager_only), db: Session = Depends(get_db)):
    return get_employees_by_department(department_id, db)


@router.get('/all')
async def get_all(user : User = Depends(hr_only), db : Session = Depends(get_db)):
   all_employees = show_all_employees(db)
   return all_employees


@router.get('/{employee_id}')
async def get_employee(employee_id : int, user : User = Depends(hr_only), db : Session = Depends(get_db)):
   employee_details = show_employee(employee_id, db)
   return employee_details

@router.post('/sign_up', response_model = EmployeeOut)
async def register(employee: EmployeeCreate, user : User = Depends(hr_only), db : Session = Depends(get_db)) :
   new_employee =  create_employee(employee, db)
   return new_employee


@router.patch('/{employee_id}/update')
async def update_info(employee_id : int , employee: EmployeeUpdate, user : User = Depends(hr_only), db : Session = Depends(get_db)):
   employee_change = update_employee(employee_id, employee, db)
   return employee_change


# soft delete — sets employment_status to "terminated"
@router.delete('/{employee_id}/delete')
async def remove_employee(employee_id: int, user: User = Depends(hr_only), db: Session = Depends(get_db)):
    return delete_employee(employee_id, db)


# hard delete — permanently removes the employee record (admin only)
@router.delete('/{employee_id}/hard-delete')
async def permanent_delete(employee_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    return hard_delete_employee(employee_id, db)
