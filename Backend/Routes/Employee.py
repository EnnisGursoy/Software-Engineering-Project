from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from Backend.Utility.dependencies import get_db
from Backend.Models.Employee import Employee
from Backend.Schemas.Employee import EmployeeCreate

router = APIRouter()


@router.post("/create", status_code=201)
async def register(employee: EmployeeCreate, db: Session = Depends(get_db)):

    # Check if SSN already exists
    existing_employee = db.query(Employee).filter(Employee.ssn == employee.ssn).first()
    if existing_employee:
        raise HTTPException(
            status_code=400,
            detail="Employee with this SSN already exists"
        )

    # Create new employee
    new_employee = Employee(
        first_name=employee.first_name,
        last_name=employee.last_name,
        email=employee.email,
        phone=employee.phone,
        address=employee.address,
        city=employee.city,
        state=employee.state,
        zip_code=employee.zip_code,
        date_of_birth=employee.date_of_birth,
        hire_date=employee.hire_date,
        termination_date=None,
        ssn=employee.ssn,
        employment_status=employee.employment_status
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return {
        "message": "Employee created successfully",
        "employee_id": new_employee.employee_id
    }