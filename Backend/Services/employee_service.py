import re
from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.Employee import Employee
from Backend.Models.Paychecks import Paychecks
from Backend.Models.Time_entries import TimeEntries
from Backend.Models.Tax_information import TaxInformation
from Backend.Models.employee_position import EmployeePosition
from Backend.Models.Department import Department
from Backend.Utility.security import encrypt_ssn, hash_password
from Backend.Schemas.Employee import EmployeeCreate, EmployeeUpdate
from datetime import date
from Backend.Models.User import User


def validate_ssn_format(ssn: str):
    """Validate SSN format (AAA-BB-CCCC) and reject known invalid number ranges."""
    if not re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
        raise HTTPException(status_code=403, detail="SSN must be in format AAA-BB-CCCC")
    area, group, serial = ssn.split('-')
    if area in ('000', '666') or area.startswith('9'):
        raise HTTPException(status_code=403, detail="Invalid SSN: invalid area number")
    if group == '00':
        raise HTTPException(status_code=403, detail="Invalid SSN: invalid group number")
    if serial == '0000':
        raise HTTPException(status_code=403, detail="Invalid SSN: invalid serial number")


def validate_name(first: str, last: str, db: Session):
    existing = (
        db.query(Employee)
        .filter(Employee.first_name == first, Employee.last_name == last)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Employee with this name already exists"
        )



def duplicate_ssn(social_security: str, db: Session):
    ssn_exists = db.query(Employee).filter(Employee.ssn == social_security).first()
    if ssn_exists:
        raise HTTPException(
            status_code=400,
            detail="Employees cannot have the same Social security number"
        )



def create_employee(data: EmployeeCreate, db: Session):
    # 1. Handle first-user-ever admin logic
    # 2. Resolve department (must already exist)
    department_id = None
    if data.department_name:
        dept = db.query(Department).filter(
            Department.department_name == data.department_name
        ).first()
        if not dept:
            raise HTTPException(status_code=404, detail=f"Department '{data.department_name}' not found")
        department_id = dept.department_id

    # 3. Validate SSN format and check for duplicates before creating any records
    validate_ssn_format(data.ssn)
    duplicate_ssn(data.ssn, db)
    encrypted = encrypt_ssn(data.ssn)

    # 4. Optionally create a linked User account
    user_id = None
    if data.user is not None:
        total_users = db.query(User).count()
        if total_users == 0:
            data.user.role = "admin"

        existing_user = db.query(User).filter(User.username == data.user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = hash_password(data.user.password)
        new_user = User(
            username=data.user.username,
            password_hash=hashed_password,
            role=data.user.role,
            department_id=department_id,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user_id = new_user.user_id

    # 5. Create Employee
    employee = Employee(
        first_name=data.first_name,
        last_name=data.last_name,
        ssn=encrypted,
        email=data.email,
        phone=data.phone,
        address=data.address,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        date_of_birth=data.date_of_birth,
        hire_date=data.hire_date,
        employment_status=data.employment_status,
        department_id=department_id,
        user_id=user_id,
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return employee



def show_employee(id: int, db: Session):
    user_exist = db.query(Employee).filter(Employee.employee_id == id).first()
    if not user_exist:
        raise HTTPException(status_code=400, detail='User does not exist in database')
    return user_exist



def show_all_employees(db: Session):
    return db.query(Employee).all()



def update_employee(id: int, data: EmployeeUpdate, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == id).first()

    if not employee:
        raise HTTPException(status_code=400, detail='User does not exist in database')

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(employee, key, value)

    db.commit()
    db.refresh(employee)
    return employee



def get_employees_by_department(department_id: int, db: Session):
    return (
        db.query(Employee)
        .filter(Employee.department_id == department_id)
        .all()
    )


def hard_delete_employee(id: int, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == id).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee does not exist in the database"
        )

    # Remove all child records before deleting the employee to avoid FK constraint errors
    db.query(TimeEntries).filter(TimeEntries.employee_id == id).delete()
    db.query(TimeEntries).filter(TimeEntries.approved_by == id).update({"approved_by": None})
    db.query(Paychecks).filter(Paychecks.employee_id == id).delete()
    db.query(TaxInformation).filter(TaxInformation.employee_id == id).delete()
    db.query(EmployeePosition).filter(EmployeePosition.employee_id == id).delete()
    db.query(Department).filter(Department.manager_id == id).update({"manager_id": None})

    db.delete(employee)
    db.commit()
    return {"message": "Employee permanently deleted"}


def delete_employee(id: int, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == id).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee does not exist in the database"
        )
    

    if employee.employment_status == "terminated":
       return {"message": "Employee is already terminated"}
    
    else :
         employee.employment_status = "terminated"

    db.commit()
    db.refresh(employee)

    return {"message": "Employee terminated successfully"}

    

    

   