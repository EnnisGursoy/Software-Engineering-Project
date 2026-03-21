from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, admin_only, hr_only, manager_only
from Backend.Models.User import User
from Backend.Models.department import Department
from Backend.Schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from Backend.Services.Department_service import show_department, get_department_by_manager_id, assign_manager, create_department, delete_department, get_my_department



router  = APIRouter()


@router.post('/create', response_model=DepartmentOut)
async def create_dept(data: DepartmentCreate, user: User = Depends(hr_only), db: Session = Depends(get_db)):
    return create_department(data, db)

@router.get('/mine')
async def get_my_dept(user: User = Depends(manager_only), db: Session = Depends(get_db)):
    return get_my_department(user, db)


@router.get('/')
async def get_all(user : User = Depends(manager_only), db : Session = Depends(get_db)):
    return show_department(db)

@router.get('/{manager_id}')
async def get_by_manager_id(manager_id : int, user : User = Depends(manager_only), db : Session = Depends(get_db)):
    return get_department_by_manager_id(manager_id, db)


@router.delete("/{department_id}")
async def remove_department(department_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    return delete_department(department_id, db)


@router.patch("/{department_id}")
async def manager_assign(
    department_id: int,
    department: DepartmentUpdate,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db)
):
    if department.manager_id is None:
        raise HTTPException(status_code=400, detail="manager_id is required to assign a manager")
    return assign_manager(
        department.manager_id,
        department_id,
        department,
        db
    )
