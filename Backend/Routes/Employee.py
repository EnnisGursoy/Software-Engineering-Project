from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, admin_only, manager_or_hr_read, get_current_employee
from Backend.Models.Employee import Employee
from Backend.Models.User import User
from Backend.Schemas.Employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from Backend.Services.employee_service import (
    create_employee,
    update_employee,
    show_employee,
    show_all_employees,
    delete_employee,
    purge_employee,
    get_employees_by_department,
    _generate_temp_password,
)
from Backend.Utility.security import hash_password

router = APIRouter()

@router.get('/by-department/{department_id}', response_model=list[EmployeeOut])
async def get_by_department(department_id: int, user: User = Depends(manager_or_hr_read), db: Session = Depends(get_db)):
    return get_employees_by_department(department_id, db)


@router.get('/me', response_model=EmployeeOut)
async def get_my_profile(employee: Employee = Depends(get_current_employee)):
    return employee


@router.patch('/me', response_model=EmployeeOut)
async def update_my_profile(
    data: EmployeeUpdate,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    return update_employee(employee.employee_id, data, db)


@router.get('/all', response_model=list[EmployeeOut])
async def get_all(user : User = Depends(manager_or_hr_read), db : Session = Depends(get_db)):
   all_employees = show_all_employees(db)
   return all_employees


@router.get('/{employee_id}')
async def get_employee(employee_id : int, user : User = Depends(hr_only), db : Session = Depends(get_db)):
   employee_details = show_employee(employee_id, db)
   return employee_details

@router.post('/sign_up')
async def register(employee: EmployeeCreate, user : User = Depends(hr_only), db : Session = Depends(get_db)) :
   """Create an employee. When no `user` block is supplied, a login is
   auto-provisioned (username = email, role = "employee") and the temp
   password is returned ONCE so the admin can hand it to the new hire."""
   new_employee, temp_password = create_employee(employee, db)
   payload = EmployeeOut.model_validate(new_employee).model_dump()
   payload["temp_password"] = temp_password
   payload["login_username"] = employee.email if temp_password else None
   return payload


@router.patch('/{employee_id}/update')
async def update_info(employee_id : int , employee: EmployeeUpdate, user : User = Depends(hr_only), db : Session = Depends(get_db)):
   employee_change = update_employee(employee_id, employee, db)
   return employee_change


@router.post('/{employee_id}/generate-login')
async def generate_employee_login(
    employee_id: int,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    """Provision a login for an employee that doesn't have one (legacy data
    pre-FR-2). Returns the temp password ONCE so the admin can share it.

    Refuses if the employee already has a linked User — use the existing
    'Reset Password' flow for those instead. Email/username collisions
    return 409 so the admin can decide how to proceed.
    """
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.user_id:
        raise HTTPException(
            status_code=400,
            detail="Employee already has a login. Use Reset Password instead.",
        )
    if not employee.email:
        raise HTTPException(status_code=400, detail="Employee has no email on file")

    if db.query(User).filter(User.username == employee.email).first():
        raise HTTPException(
            status_code=409,
            detail=f"Username '{employee.email}' is already taken.",
        )

    temp_password = _generate_temp_password()
    new_user = User(
        username=employee.email,
        password_hash=hash_password(temp_password),
        role="employee",
        first_name=employee.first_name,
        last_name=employee.last_name,
        department_id=employee.department_id,
        is_active=True,
    )
    db.add(new_user)
    db.flush()
    employee.user_id = new_user.user_id
    db.commit()

    return {
        "employee_id": employee.employee_id,
        "login_username": employee.email,
        "temp_password": temp_password,
    }


# soft delete — sets employment_status to "terminated"
@router.delete('/{employee_id}/delete')
async def remove_employee(employee_id: int, user: User = Depends(hr_only), db: Session = Depends(get_db)):
    return delete_employee(employee_id, db)


# purge — permanently removes the employee record and dependent rows (admin only)
@router.delete('/{employee_id}/purge')
async def purge_record(employee_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    return purge_employee(employee_id, db)
