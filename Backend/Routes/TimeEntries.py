from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_only, admin_or_manager
from Backend.Models.User import User
from Backend.Schemas.TimeEntry import TimeEntryCreate, TimeEntryOut, TimeEntryUpdate, TimeEntryApprove
from Backend.Services.timeentry_service import (
    create_time_entry,
    get_entries_by_employee,
    get_all_entries,
    get_pending_approvals,
    update_time_entry,
    approve_time_entry,
    delete_time_entry,
)

router = APIRouter()


@router.get("/all", response_model=list[TimeEntryOut])
async def list_all_entries(
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_all_entries(db)


@router.get("/pending", response_model=list[TimeEntryOut])
async def list_pending(
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_pending_approvals(db)


@router.get("/employee/{employee_id}", response_model=list[TimeEntryOut])
async def entries_for_employee(
    employee_id: int,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_entries_by_employee(employee_id, db)


@router.post("/create", response_model=TimeEntryOut)
async def add_entry(
    entry: TimeEntryCreate,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return create_time_entry(entry, db)


@router.patch("/{entry_id}", response_model=TimeEntryOut)
async def edit_entry(
    entry_id: int,
    data: TimeEntryUpdate,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return update_time_entry(entry_id, data, db)


@router.patch("/{entry_id}/approve", response_model=TimeEntryOut)
async def approve_entry(
    entry_id: int,
    data: TimeEntryApprove,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return approve_time_entry(entry_id, data, db, user)


@router.delete("/{entry_id}")
async def remove_entry(
    entry_id: int,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return delete_time_entry(entry_id, db)
