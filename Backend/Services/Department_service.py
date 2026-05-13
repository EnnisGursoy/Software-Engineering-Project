from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.Department import Department
from Backend.Models.Employee import Employee
from Backend.Models.Positions import Positions
from Backend.Models.User import User
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


def _resolve_manager(department: Department, db: Session) -> dict:
    """Resolve the manager for a department from two sources.

    1. `departments.manager_id` (FK → employees.employee_id) — the "official"
       link, used when the manager has an Employee record.
    2. Fallback: any User with role='manager' and matching department_id —
       covers manager-role users created via Settings → Create User who
       never had an Employee row.

    When the fallback finds a manager whose User row is linked to an
    Employee, we auto-fill departments.manager_id once so the link
    persists in MySQL (the "make their id occur in the database" fix).
    Returns the manager's display name, the FK-eligible employee_id, and
    the underlying user_id (useful for the UI).
    """
    manager_name = None
    manager_user_id = None

    # Source 1 — official FK
    if department.manager_id:
        emp = db.query(Employee).filter(Employee.employee_id == department.manager_id).first()
        if emp:
            manager_name = f"{emp.first_name} {emp.last_name}".strip()
            if emp.user_id:
                manager_user_id = emp.user_id

    # Source 2 — manager-role user pinned to this department
    if manager_name is None:
        user_mgr = (
            db.query(User)
            .filter(User.role == "manager", User.department_id == department.department_id)
            .first()
        )
        if user_mgr:
            full = f"{user_mgr.first_name or ''} {user_mgr.last_name or ''}".strip()
            manager_name = full or user_mgr.username
            manager_user_id = user_mgr.user_id

            # If this manager-user happens to have an Employee row, write
            # the FK so subsequent reads come from Source 1 directly.
            linked_emp = db.query(Employee).filter(Employee.user_id == user_mgr.user_id).first()
            if linked_emp and not department.manager_id:
                department.manager_id = linked_emp.employee_id

    return {
        "department_id": department.department_id,
        "department_name": department.department_name,
        "manager_id": department.manager_id,
        "manager_user_id": manager_user_id,
        "manager_name": manager_name,
    }


def show_department(db: Session):
    departments = db.query(Department).all()
    payload = [_resolve_manager(d, db) for d in departments]
    db.commit()  # persist any auto-filled manager_id FKs
    return payload
    
def get_department_by_manager_id (data : int , db : Session):
    manager_department = db.query(Department).filter(Department.manager_id == data).first()

    if not manager_department:
        raise HTTPException(status_code = 400, detail="Manager does not manage any department")
    
    else :
        return manager_department
    

def delete_department(department_id: int, db: Session):
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Nullify department_id on positions before deleting to avoid FK constraint error
    db.query(Positions).filter(Positions.department_id == department_id).update({"department_id": None})

    db.delete(department)
    db.commit()
    return {"message": "Department permanently deleted"}


def get_my_department(user, db: Session):
    if not user.department_id:
        raise HTTPException(
            status_code=400,
            detail="Your account is not assigned to a department. Ask an admin to update your account."
        )

    department = db.query(Department).filter(
        Department.department_id == user.department_id
    ).first()
    if not department:
        raise HTTPException(status_code=404, detail="Your assigned department no longer exists")

    return department


def assign_manager(manager_id: int, department_id: int, data: DepartmentUpdate, db: Session):
    # Check department exists
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=400, detail="Department does not exist")

    # Check manager exists
    manager = db.query(Employee).filter(Employee.employee_id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(department, key, value)

    # Assign manager
    department.manager_id = manager_id

    # Two-way sync: if the new manager has a linked User row, pin that user
    # to the same department. Keeps users.department_id in step so the
    # departments page (and "my department" lookups) stay consistent.
    if manager.user_id:
        user_row = db.query(User).filter(User.user_id == manager.user_id).first()
        if user_row:
            user_row.department_id = department_id

    db.commit()
    db.refresh(department)

    return department
       






