from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_only, manager_or_hr_read
from Backend.Models.User import User
from Backend.Schemas.PayPeriod import PayPeriodCreate, PayPeriodOut, PayPeriodStatusUpdate
from Backend.Services.PayPeriod_service import (
    get_all_pay_periods,
    get_pay_period,
    create_pay_period,
    update_pay_period_status,
    delete_pay_period,
)

router = APIRouter()


@router.get("/all", response_model=list[PayPeriodOut])
async def list_periods(
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    return get_all_pay_periods(db)


@router.get("/{pay_period_id}", response_model=PayPeriodOut)
async def get_one(
    pay_period_id: int,
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    return get_pay_period(pay_period_id, db)


@router.post("/create", response_model=PayPeriodOut)
async def create(
    data: PayPeriodCreate,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return create_pay_period(data, db)


@router.patch("/{pay_period_id}/status", response_model=PayPeriodOut)
async def update_status(
    pay_period_id: int,
    data: PayPeriodStatusUpdate,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return update_pay_period_status(pay_period_id, data, db)


@router.delete("/{pay_period_id}")
async def delete(
    pay_period_id: int,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return delete_pay_period(pay_period_id, db)
