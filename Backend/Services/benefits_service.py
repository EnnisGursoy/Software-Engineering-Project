from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.BenefitPlan import BenefitPlan
from Backend.Models.BenefitEnrollment import BenefitEnrollment
from Backend.Schemas.Benefits import PlanCreate, PlanUpdate, EnrollmentCreate, EnrollmentUpdate


# ── PLANS ──────────────────────────────────────────────────────────────────────

def get_all_plans(db: Session):
    return db.query(BenefitPlan).all()


def get_plan(plan_id: int, db: Session):
    p = db.query(BenefitPlan).filter(BenefitPlan.plan_id == plan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Plan not found")
    return p


def create_plan(data: PlanCreate, db: Session):
    plan = BenefitPlan(**data.dict())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(plan_id: int, data: PlanUpdate, db: Session):
    plan = get_plan(plan_id, db)
    for key, value in data.dict(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(plan_id: int, db: Session):
    plan = get_plan(plan_id, db)
    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted"}


# ── ENROLLMENTS ────────────────────────────────────────────────────────────────

def get_all_enrollments(db: Session):
    return db.query(BenefitEnrollment).all()


def get_enrollments_by_employee(employee_id: int, db: Session):
    return db.query(BenefitEnrollment).filter(
        BenefitEnrollment.employee_id == employee_id
    ).all()


def create_enrollment(data: EnrollmentCreate, db: Session):
    enrollment = BenefitEnrollment(**data.dict())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def update_enrollment(enrollment_id: int, data: EnrollmentUpdate, db: Session):
    enrollment = db.query(BenefitEnrollment).filter(
        BenefitEnrollment.enrollment_id == enrollment_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(enrollment, key, value)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def delete_enrollment(enrollment_id: int, db: Session):
    enrollment = db.query(BenefitEnrollment).filter(
        BenefitEnrollment.enrollment_id == enrollment_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    db.delete(enrollment)
    db.commit()
    return {"message": "Enrollment deleted"}
