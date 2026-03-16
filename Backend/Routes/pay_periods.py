from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, admin_only, admin_or_manager
from Backend.Models.User import User
from Backend.Schemas.PayPeriods import PayPeriodCreate, PayPeriodUpdate, PayPeriodOut
from Backend.Services.PayPeriod_service import (
    get_all_pay_periods, get_pay_period,
    create_pay_period, update_pay_period, close_pay_period
)

router = APIRouter(tags=["Pay Periods"])


@router.get("/", response_model=list[PayPeriodOut])
@router.get("/all", response_model=list[PayPeriodOut])
async def list_all(db: Session = Depends(get_db), user: User = Depends(hr_only)):
    return get_all_pay_periods(db)


@router.get("/{pay_period_id}", response_model=PayPeriodOut)
async def get_one(pay_period_id: int, db: Session = Depends(get_db), user: User = Depends(hr_only)):
    return get_pay_period(pay_period_id, db)


@router.post("/", response_model=PayPeriodOut)
async def create(data: PayPeriodCreate, db: Session = Depends(get_db), user: User = Depends(admin_or_manager)):
    return create_pay_period(data, db)


@router.patch("/{pay_period_id}", response_model=PayPeriodOut)
async def update(pay_period_id: int, data: PayPeriodUpdate, db: Session = Depends(get_db), user: User = Depends(admin_or_manager)):
    return update_pay_period(pay_period_id, data, db)


@router.patch("/{pay_period_id}/close")
async def close(pay_period_id: int, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return close_pay_period(pay_period_id, db)
