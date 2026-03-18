from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_only, admin_or_manager
from Backend.Models.User import User
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
)

router = APIRouter()


@router.get("/all", response_model=list[PaycheckOut])
async def list_all_paychecks(
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_all_paychecks(db)


@router.get("/periods")
async def list_pay_periods(
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_all_pay_periods(db)


@router.get("/employee/{employee_id}", response_model=list[PaycheckOut])
async def paychecks_for_employee(
    employee_id: int,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_paychecks_by_employee(employee_id, db)


@router.get("/period/{pay_period_id}", response_model=list[PaycheckOut])
async def paychecks_for_period(
    pay_period_id: int,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_paychecks_by_period(pay_period_id, db)


@router.get("/calculate/{employee_id}/{pay_period_id}")
async def preview_paycheck(
    employee_id: int,
    pay_period_id: int,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return calculate_paycheck(employee_id, pay_period_id, db)


@router.post("/run/{pay_period_id}")
async def process_payroll(
    pay_period_id: int,
    user: User = Depends(admin_or_manager),
    db: Session = Depends(get_db),
):
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
