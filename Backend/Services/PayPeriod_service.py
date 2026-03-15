from fastapi import HTTPException
from sqlalchemy.orm import Session
from Backend.Models.pay_periods import PayPeriods


def get_all_pay_periods(db: Session):
    return db.query(PayPeriods).order_by(PayPeriods.period_start_date.desc()).all()


def get_pay_period(pay_period_id: int, db: Session):
    period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")
    return period


def create_pay_period(data, db: Session):
    # Prevent overlapping open/processing periods of the same type
    overlap = (
        db.query(PayPeriods)
        .filter(
            PayPeriods.period_type == data.period_type,
            PayPeriods.status.in_(["open", "processing"]),
            PayPeriods.period_start_date <= data.period_end_date,
            PayPeriods.period_end_date >= data.period_start_date,
        )
        .first()
    )
    if overlap:
        raise HTTPException(
            status_code=409,
            detail=f"An active pay period of type '{data.period_type}' already overlaps those dates"
        )

    period = PayPeriods(**data.model_dump())
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def update_pay_period(pay_period_id: int, data, db: Session):
    period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Pay period not found")

    if period.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot modify a closed pay period")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(period, key, value)

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
