from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.pay_periods import PayPeriods
from Backend.Schemas.PayPeriods import PayPeriodCreate, PayPeriodUpdate, PayPeriodStatusUpdate

VALID_PERIOD_TYPES = {"weekly", "bi_weekly", "semi_monthly", "monthly"}
VALID_STATUSES     = {"open", "processing", "paid", "closed"}


def get_all_pay_periods(db: Session):
    return db.query(PayPeriods).order_by(PayPeriods.period_start_date.desc()).all()


def get_pay_period(pay_period_id: int, db: Session):
    period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")
    return period


def create_pay_period(data: PayPeriodCreate, db: Session):
    if data.period_type not in VALID_PERIOD_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid period type. Choose from: {VALID_PERIOD_TYPES}")

    if data.period_end_date <= data.period_start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    if data.pay_date < data.period_end_date:
        raise HTTPException(status_code=400, detail="Pay date must be on or after end date")

# Check for overlapping open periods of the same type
    overlap = db.query(PayPeriods).filter(
        PayPeriods.status.in_(["open", "processing"]),
        PayPeriods.period_type == data.period_type,
        PayPeriods.period_start_date <= data.period_end_date,
        PayPeriods.period_end_date >= data.period_start_date,
    ).first()
    if overlap:
        raise HTTPException(
            status_code=409,
            detail=f"Overlaps with existing open pay period (ID {overlap.pay_period_id})"
        )

    period = PayPeriods(
        period_start_date=data.period_start_date,
        period_end_date=data.period_end_date,
        pay_date=data.pay_date,
        period_type=data.period_type,
        status="open",
    )
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def update_pay_period_status(pay_period_id: int, data: PayPeriodStatusUpdate, db: Session):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {VALID_STATUSES}")

    period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")

    period.status = data.status
    db.commit()
    db.refresh(period)
    return period


def delete_pay_period(pay_period_id: int, db: Session):
    period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")

    if period.status != "open":
        raise HTTPException(status_code=400, detail="Only open pay periods can be deleted")

    db.delete(period)
    db.commit()
    return {"message": "Pay period deleted"}

def update_pay_period(pay_period_id: int, data, db: Session):
    period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")
    if period.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot update a closed pay period")
    if data.pay_date is not None:
        period.pay_date = data.pay_date
    if data.status is not None:
        period.status = data.status
    if data.period_start_date is not None:
        period.period_start_date = data.period_start_date
    if data.period_end_date is not None:
        period.period_end_date = data.period_end_date
    if data.period_type is not None:
        period.period_type = data.period_type
    db.commit()
    db.refresh(period)
    return period


def close_pay_period(pay_period_id: int, db: Session):
    period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")
    if period.status == "closed":
        return {"message": "Pay period is already closed"}
    period.status = "closed"
    db.commit()
    db.refresh(period)
    return {"message": "Pay period closed successfully"}

