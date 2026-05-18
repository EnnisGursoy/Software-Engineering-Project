from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_or_hr_read, admin_or_manager, get_current_employee
from Backend.Models.Employee import Employee
from Backend.Models.User import User
from Backend.Models.Paychecks import Paychecks
from Backend.Models.pay_periods import PayPeriods
from Backend.Schemas.Paycheck import PaycheckCreate, PaycheckOut, PaycheckStatusUpdate
from Backend.Services.paycheck_service import (
    create_paycheck,
    run_payroll,
    calculate_paycheck,
    get_all_paychecks,
    get_paychecks_by_employee,
    get_paychecks_by_period,
    get_all_pay_periods,
    update_paycheck_status,
    get_paychecks_for_manager,
    get_paychecks_for_manager_by_period,
    get_paychecks_for_employee_ids,
    get_paychecks_for_employee_ids_by_period,
    get_managed_employee_ids,
    get_managed_employee_ids_for_user,
)
from Backend.Services.paycheck_pdf import render_paystub_pdf
from Backend.Services.payroll_report_pdf import render_payroll_report_pdf

router = APIRouter()


def _build_paystub_response(paycheck: Paychecks, employee: Employee, db: Session) -> Response:
    """Render a paycheck as a PDF and wrap it in a download response."""
    period = db.query(PayPeriods).filter(
        PayPeriods.pay_period_id == paycheck.pay_period_id
    ).first()
    pdf_bytes = render_paystub_pdf(paycheck, employee, period)
    filename = (
        f"paystub_{employee.last_name}_{paycheck.paycheck_id}.pdf"
        .replace(" ", "_")
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/me", response_model=list[PaycheckOut])
async def my_paychecks(
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    return get_paychecks_by_employee(employee.employee_id, db)


@router.get("/me/{paycheck_id}/pdf")
async def my_paystub_pdf(
    paycheck_id: int,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    """Download the logged-in employee's own pay stub as a PDF.
    Refuses any paycheck that doesn't belong to the caller."""
    paycheck = db.query(Paychecks).filter(Paychecks.paycheck_id == paycheck_id).first()
    if not paycheck or paycheck.employee_id != employee.employee_id:
        raise HTTPException(status_code=404, detail="Paycheck not found")
    return _build_paystub_response(paycheck, employee, db)


@router.get("/{paycheck_id}/pdf")
async def paystub_pdf_admin(
    paycheck_id: int,
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    """Admin/manager/HR-side download for any employee's pay stub."""
    paycheck = db.query(Paychecks).filter(Paychecks.paycheck_id == paycheck_id).first()
    if not paycheck:
        raise HTTPException(status_code=404, detail="Paycheck not found")
    employee = db.query(Employee).filter(Employee.employee_id == paycheck.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if user.role == "manager":
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if paycheck.employee_id not in allowed_ids:
            raise HTTPException(status_code=404, detail="Paycheck not found")

    return _build_paystub_response(paycheck, employee, db)


@router.get("/all", response_model=list[PaycheckOut])
async def list_all_paychecks(
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    """List paychecks. Managers see only their subordinates' paychecks; HR/Admin see all."""

    if user.role in ['admin', 'hr']:
        return get_all_paychecks(db)

    allowed_ids = get_managed_employee_ids_for_user(user, db)
    if not allowed_ids:
        return []

    return get_paychecks_for_employee_ids(allowed_ids, db)


@router.get("/report-pdf")
async def payroll_summary_report_pdf(
    pay_period_id: int | None = None,
    status: str | None = None,
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    """Server-side PDF of the Payroll Summary report (FR-15).

    Filters mirror the UI: optional pay_period_id and payment status. The
    PDF lists every matching paycheck with totals at the bottom, then
    streams as `application/pdf` so the browser downloads it.
    """
    q = db.query(Paychecks)
    if pay_period_id is not None:
        q = q.filter(Paychecks.pay_period_id == pay_period_id)
    if status:
        q = q.filter(Paychecks.payment_status == status)

    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        q = q.filter(Paychecks.employee_id.in_(allowed_ids))

    paychecks = q.order_by(Paychecks.pay_period_id, Paychecks.paycheck_id).all()

    # Join employee + period info so the PDF can show real names and
    # period date ranges rather than raw IDs.
    emp_ids = {p.employee_id for p in paychecks}
    employees = {
        e.employee_id: e
        for e in db.query(Employee).filter(Employee.employee_id.in_(emp_ids)).all()
    } if emp_ids else {}

    period_ids = {p.pay_period_id for p in paychecks}
    periods = {
        pp.pay_period_id: pp
        for pp in db.query(PayPeriods).filter(PayPeriods.pay_period_id.in_(period_ids)).all()
    } if period_ids else {}

    rows = []
    totals = {"gross": 0.0, "fed": 0.0, "state": 0.0,
              "fica": 0.0, "other": 0.0, "net": 0.0}
    for p in paychecks:
        emp = employees.get(p.employee_id)
        per = periods.get(p.pay_period_id)
        emp_name = f"{emp.first_name} {emp.last_name}" if emp else f"Employee #{p.employee_id}"
        if per:
            period_label = f"{per.period_start_date} – {per.period_end_date}"
        else:
            period_label = f"Period #{p.pay_period_id}"
        fica  = float(p.social_security or 0) + float(p.medicare or 0)
        other = float(p.health_insurance or 0) + float(p.retirement_401k or 0) + float(p.other_deductions or 0)
        rows.append({
            "employee": emp_name,
            "period":   period_label,
            "gross":    p.gross_pay or 0,
            "fed":      p.federal_tax or 0,
            "state":    p.state_tax or 0,
            "fica":     fica,
            "other":    other,
            "net":      p.net_pay or 0,
            "status":   p.payment_status,
        })
        totals["gross"] += float(p.gross_pay or 0)
        totals["fed"]   += float(p.federal_tax or 0)
        totals["state"] += float(p.state_tax or 0)
        totals["fica"]  += fica
        totals["other"] += other
        totals["net"]   += float(p.net_pay or 0)

    # Human-readable filter line for the report header
    parts = []
    if pay_period_id is not None and pay_period_id in periods:
        per = periods[pay_period_id]
        parts.append(f"Pay period {per.period_start_date} – {per.period_end_date}")
    elif pay_period_id is not None:
        parts.append(f"Pay period #{pay_period_id}")
    else:
        parts.append("All pay periods")
    if status:
        parts.append(f"status = {status}")
    filter_text = ", ".join(parts)

    pdf_bytes = render_payroll_report_pdf(rows, totals, filter_text)
    filename = (
        f"payroll_report_period{pay_period_id}.pdf"
        if pay_period_id is not None
        else "payroll_report_all.pdf"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/periods")
async def list_pay_periods(
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    return get_all_pay_periods(db)


@router.get("/employee/{employee_id}", response_model=list[PaycheckOut])
async def paychecks_for_employee(
    employee_id: int,
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if employee_id not in allowed_ids:
            raise HTTPException(status_code=404, detail="Employee not found")
    return get_paychecks_by_employee(employee_id, db)


@router.get("/period/{pay_period_id}", response_model=list[PaycheckOut])
async def paychecks_for_period(
    pay_period_id: int,
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    """Get paychecks for a period. Managers see only their subordinates; HR/Admin see all."""
    # Verify period exists first
    period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")

    # If user is admin or HR, show all paychecks for this period
    if user.role in ['admin', 'hr']:
        return get_paychecks_by_period(pay_period_id, db)

    # If user is a manager, filter to their subordinates
    allowed_ids = get_managed_employee_ids_for_user(user, db)
    return get_paychecks_for_employee_ids_by_period(allowed_ids, pay_period_id, db)


@router.get("/calculate/{employee_id}/{pay_period_id}")
async def preview_paycheck(
    employee_id: int,
    pay_period_id: int,
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if employee_id not in allowed_ids:
            raise HTTPException(status_code=404, detail="Employee not found")
    return calculate_paycheck(employee_id, pay_period_id, db)


@router.post("/run/{pay_period_id}")
async def process_payroll(
    pay_period_id: int,
    user: User = Depends(admin_or_manager),
    db: Session = Depends(get_db),
):
    if user.role == 'manager':
        allowed_ids = get_managed_employee_ids_for_user(user, db)
        if not allowed_ids:
            return {'paychecks_created': 0, 'pay_period_id': pay_period_id}
        return run_payroll(pay_period_id, db, employee_ids=allowed_ids)
    return run_payroll(pay_period_id, db)


@router.post("/create", response_model=PaycheckOut)
async def add_paycheck(
    paycheck: PaycheckCreate,
    user: User = Depends(admin_or_manager),
    db: Session = Depends(get_db),
):
    return create_paycheck(paycheck, db)


@router.patch("/{paycheck_id}/status", response_model=PaycheckOut)
async def set_paycheck_status(
    paycheck_id: int,
    data: PaycheckStatusUpdate,
    user: User = Depends(admin_or_manager),
    db: Session = Depends(get_db),
):
    return update_paycheck_status(paycheck_id, data, db)
