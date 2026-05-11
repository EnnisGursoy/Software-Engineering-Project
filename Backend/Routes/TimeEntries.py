from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_only, manager_or_hr_read, get_current_employee
from Backend.Models.Employee import Employee
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


@router.get("/me", response_model=list[TimeEntryOut])
async def my_time_entries(
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    return get_entries_by_employee(employee.employee_id, db)


@router.post("/me", response_model=TimeEntryOut)
async def submit_my_time_entry(
    data: TimeEntryCreate,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    data.employee_id = employee.employee_id
    return create_time_entry(data, db)


@router.get("/all", response_model=list[TimeEntryOut])
async def list_all_entries(
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    return get_all_entries(db)


@router.get("/pending", response_model=list[TimeEntryOut])
async def list_pending(
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    return get_pending_approvals(db)


@router.get("/employee/{employee_id}", response_model=list[TimeEntryOut])
async def entries_for_employee(
    employee_id: int,
    user: User = Depends(manager_or_hr_read),
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
    # Body is accepted for shape compatibility but the approver is the
    # authenticated user — never trust the client to declare who approved.
    # `approved_by` is nullable; if the HR/admin user has no linked Employee
    # record, approve the entry without recording an approver.
    approver = db.query(Employee).filter(Employee.user_id == user.user_id).first()
    approver_id = approver.employee_id if approver else None
    return approve_time_entry(entry_id, approver_id, db)


@router.delete("/{entry_id}")
async def remove_entry(
    entry_id: int,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return delete_time_entry(entry_id, db)
