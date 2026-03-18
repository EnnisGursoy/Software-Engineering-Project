from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_only
from Backend.Models.User import User
from Backend.Schemas.Position import (
    PositionCreate, PositionOut, PositionUpdate,
    EmployeePositionCreate, EmployeePositionOut,
)
from Backend.Services.Position_service import (
    get_all_positions,
    get_position,
    create_position,
    update_position,
    delete_position,
    assign_position_to_employee,
    get_positions_by_employee,
)

router = APIRouter()


@router.get("/all", response_model=list[PositionOut])
async def list_positions(
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_all_positions(db)


@router.get("/{position_id}", response_model=PositionOut)
async def get_one(
    position_id: int,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_position(position_id, db)


@router.post("/create", response_model=PositionOut)
async def create(
    data: PositionCreate,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return create_position(data, db)


@router.patch("/{position_id}", response_model=PositionOut)
async def update(
    position_id: int,
    data: PositionUpdate,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return update_position(position_id, data, db)


@router.delete("/{position_id}")
async def delete(
    position_id: int,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return delete_position(position_id, db)


@router.post("/assign", response_model=EmployeePositionOut)
async def assign_to_employee(
    data: EmployeePositionCreate,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return assign_position_to_employee(data, db)


@router.get("/employee/{employee_id}", response_model=list[EmployeePositionOut])
async def employee_positions(
    employee_id: int,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_positions_by_employee(employee_id, db)
