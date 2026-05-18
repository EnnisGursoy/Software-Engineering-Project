from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_only, manager_or_hr_read, get_current_employee, admin_or_manager
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
from Backend.Services.paycheck_service import get_managed_employee_ids_for_user

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
    """List all time entries. Managers see only their subordinates' entries; HR/Admin see all."""
    if user.role in ['admin', 'hr']:
        return get_all_entries(db)

    allowed_ids = get_managed_employee_ids_for_user(user, db)
    if not allowed_ids:
        return []

    from Backend.Models.Time_entries import TimeEntries
    return db.query(TimeEntries).filter(TimeEntries.employee_id.in_(allowed_ids)).order_by(TimeEntries.entry_date.desc()).all()


@router.get("/pending", response_model=list[TimeEntryOut])
async def list_pending(
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    """List pending time entries. Managers see only their subordinates' pending entries; HR/Admin see all."""
    if user.role in ['admin', 'hr']:
        return get_pending_approvals(db)

    allowed_ids = get_managed_employee_ids_for_user(user, db)
    if not allowed_ids:
        return []

    from Backend.Models.Time_entries import TimeEntries
    return db.query(TimeEntries).filter(
        TimeEntries.approved == False,
        TimeEntries.employee_id.in_(allowed_ids)
    ).order_by(TimeEntries.entry_date.desc()).all()


@router.get("/employee/{employee_id}", response_model=list[TimeEntryOut])
async def entries_for_employee(
    employee_id: int,
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    """Get entries for a specific employee. Managers can only view their subordinates' entries."""
    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if employee_id not in allowed_ids:
            return []

    return get_entries_by_employee(employee_id, db)


@router.post("/create", response_model=TimeEntryOut)
async def add_entry(
    entry: TimeEntryCreate,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    """Create a time entry. Managers can only create entries for their subordinates."""
    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if entry.employee_id not in allowed_ids:
            raise HTTPException(status_code=404, detail="Employee not found")

    return create_time_entry(entry, db)


@router.patch("/{entry_id}", response_model=TimeEntryOut)
async def edit_entry(
    entry_id: int,
    data: TimeEntryUpdate,
    user: User = Depends(admin_or_manager),
    db: Session = Depends(get_db),
):
    """Edit a time entry. Managers can only edit entries for their subordinates."""
    from Backend.Models.Time_entries import TimeEntries
    entry = db.query(TimeEntries).filter(TimeEntries.entry_id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if entry.employee_id not in allowed_ids:
            raise HTTPException(status_code=404, detail="Time entry not found")

    return update_time_entry(entry_id, data, db)


@router.patch("/{entry_id}/approve", response_model=TimeEntryOut)
async def approve_entry(
    entry_id: int,
    data: TimeEntryApprove,
    user: User = Depends(admin_or_manager),
    db: Session = Depends(get_db),
):
    """Approve a time entry. Managers can only approve entries for their subordinates."""
    from Backend.Models.Time_entries import TimeEntries
    entry = db.query(TimeEntries).filter(TimeEntries.entry_id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if entry.employee_id not in allowed_ids:
            raise HTTPException(status_code=404, detail="Time entry not found")

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
    user: User = Depends(admin_or_manager),
    db: Session = Depends(get_db),
):
    """Delete a time entry. Managers can only delete entries for their subordinates."""
    from Backend.Models.Time_entries import TimeEntries
    entry = db.query(TimeEntries).filter(TimeEntries.entry_id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if entry.employee_id not in allowed_ids:
            raise HTTPException(status_code=404, detail="Time entry not found")

    return delete_time_entry(entry_id, db)
