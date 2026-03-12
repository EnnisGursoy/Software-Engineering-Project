from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, admin_only, hr_only, manager_only
from Backend.Models.User import User
from Backend.Models.Department import Department
from Backend.Schemas.department import DepartmentCreate, Departmentout, DepartmentUpdate
from Backend.Services.Department_service import show_department, get_department_by_manager_id, assign_manager, create_department



router  = APIRouter()


@router.post('/create', response_model=Departmentout)
async def create_dept(data: DepartmentCreate, user: User = Depends(hr_only), db: Session = Depends(get_db)):
    return create_department(data, db)


@router.get('/')
async def get_all(user : User = Depends(manager_only), db : Session = Depends(get_db)):
    return show_department(db)

@router.get('/{manager_id}')
async def get_by_manager_id(manager_id : int, user : User = Depends(manager_only), db : Session = Depends(get_db)):
    return get_department_by_manager_id(manager_id, db)


@router.patch("/{department_id}")
async def manager_assign(
    department_id: int,
    department: DepartmentUpdate,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db)
):
    return assign_manager(
        department.manager_id,
        department_id,
        department,
        db
    )