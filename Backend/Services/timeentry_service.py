from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta
from Backend.Models.Time_entries import TimeEntries
from Backend.Models.Employee import Employee
from Backend.Schemas.TimeEntry import TimeEntryCreate, TimeEntryUpdate, TimeEntryApprove


def _calc_hours(clock_in, clock_out) -> tuple[float, float]:
    """Calculate regular and overtime hours from clock_in/clock_out time objects."""
    if not clock_in or not clock_out:
        return 0.0, 0.0
    today = datetime.today().date()
    dt_in = datetime.combine(today, clock_in)
    dt_out = datetime.combine(today, clock_out)
    if dt_out < dt_in:
        dt_out += timedelta(days=1)  # overnight shift
    total = (dt_out - dt_in).total_seconds() / 3600.0
    regular = min(total, 8.0)
    overtime = max(total - 8.0, 0.0)
    return round(regular, 2), round(overtime, 2)


def create_time_entry(data: TimeEntryCreate, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Auto-calculate hours from clock times if not provided
    regular_hours = data.regular_hours
    overtime_hours = data.overtime_hours

    if regular_hours is None and data.clock_in and data.clock_out:
        regular_hours, overtime_hours = _calc_hours(data.clock_in, data.clock_out)

    entry = TimeEntries(
        employee_id=data.employee_id,
        entry_date=data.entry_date,
        clock_in=data.clock_in,
        clock_out=data.clock_out,
        regular_hours=regular_hours,
        overtime_hours=overtime_hours,
        entry_type=data.entry_type,
        notes=data.notes,
        approved=False,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_entries_by_employee(employee_id: int, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return (
        db.query(TimeEntries)
        .filter(TimeEntries.employee_id == employee_id)
        .order_by(TimeEntries.entry_date.desc())
        .all()
    )


def get_all_entries(db: Session):
    return db.query(TimeEntries).order_by(TimeEntries.entry_date.desc()).all()


def get_pending_approvals(db: Session):
    return (
        db.query(TimeEntries)
        .filter(TimeEntries.approved == False)
        .order_by(TimeEntries.entry_date.desc())
        .all()
    )


def update_time_entry(entry_id: int, data: TimeEntryUpdate, db: Session):
    entry = db.query(TimeEntries).filter(TimeEntries.entry_id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if entry.approved:
        raise HTTPException(status_code=400, detail="Cannot edit an approved time entry")

    update_data = data.dict(exclude_unset=True)

    # Recalculate hours if clock times changed
    clock_in = update_data.get("clock_in", entry.clock_in)
    clock_out = update_data.get("clock_out", entry.clock_out)
    if ("clock_in" in update_data or "clock_out" in update_data) and "regular_hours" not in update_data:
        regular, overtime = _calc_hours(clock_in, clock_out)
        update_data["regular_hours"] = regular
        update_data["overtime_hours"] = overtime

    for key, value in update_data.items():
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return entry


def approve_time_entry(entry_id: int, data: TimeEntryApprove, db: Session):
    entry = db.query(TimeEntries).filter(TimeEntries.entry_id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    approver = db.query(Employee).filter(Employee.employee_id == data.approved_by).first()
    if not approver:
        raise HTTPException(status_code=404, detail="Approver employee not found")

    entry.approved = data.approved
    entry.approved_by = data.approved_by

    db.commit()
    db.refresh(entry)
    return entry


def delete_time_entry(entry_id: int, db: Session):
    entry = db.query(TimeEntries).filter(TimeEntries.entry_id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if entry.approved:
        raise HTTPException(status_code=400, detail="Cannot delete an approved time entry")

    db.delete(entry)
    db.commit()
    return {"message": "Time entry deleted"}
