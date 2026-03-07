from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.Department import Department
from Backend.Models.Employee import Employee
from Backend.Schemas.department import DepartmentCreate, DepartmentUpdate




def create_department (data : DepartmentCreate, db : Session):
    department_exist = db.query(Department).filter(Department.department_name == data.department_name).first()

    if department_exist :
        raise HTTPException(status_code = 400, detail = "Department exists")
    
    else :
        new_department  =  Department(
            department_name = data.department_name,
            manager_id = data.manager_id
        )

        db.add(new_department)
        db.commit()
        db.refresh(new_department)
        return new_department
    

def show_department (db : Session):
    return db.query(Department).all()
    
def get_department_by_manager_id (data : int , db : Session):
    manager_department = db.query(Department).filter(Department.manager_id == data).first()

    if not manager_department:
        raise HTTPException(status_code = 400, detail="Manager does not manage any department")
    
    else :
        return manager_department
    

def assign_manager(manager_id: int, department_id: int, data: DepartmentUpdate, db: Session):
    # Check department exists
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=400, detail="Department does not exist")

    # Check manager exists
    manager = db.query(Employee).filter(Employee.employee_id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(department, key, value)

    # Assign manager
    department.manager_id = manager_id

    db.commit()
    db.refresh(department)

    return department
       







