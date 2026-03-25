from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_only, get_current_user, get_current_employee
from Backend.Models.Employee import Employee
from Backend.Models.User import User
from Backend.Schemas.Benefits import (
    PlanCreate, PlanOut, PlanUpdate,
    EnrollmentCreate, EnrollmentOut, EnrollmentUpdate,
)
from Backend.Services.benefits_service import (
    get_all_plans, get_plan, create_plan, update_plan, delete_plan,
    get_all_enrollments, get_enrollments_by_employee,
    create_enrollment, update_enrollment, delete_enrollment,
)

router = APIRouter()


# ── PLANS ──────────────────────────────────────────────────────────────────────

@router.get("/plans/all", response_model=list[PlanOut])
async def list_plans(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_all_plans(db)


@router.post("/plans/create", response_model=PlanOut)
async def add_plan(
    data: PlanCreate,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return create_plan(data, db)


@router.patch("/plans/{plan_id}", response_model=PlanOut)
async def edit_plan(
    plan_id: int,
    data: PlanUpdate,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return update_plan(plan_id, data, db)


@router.delete("/plans/{plan_id}")
async def remove_plan(
    plan_id: int,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return delete_plan(plan_id, db)


# ── ENROLLMENTS ────────────────────────────────────────────────────────────────

@router.get("/enrollments/me", response_model=list[EnrollmentOut])
async def my_enrollments(
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    return get_enrollments_by_employee(employee.employee_id, db)


@router.get("/enrollments/all", response_model=list[EnrollmentOut])
async def list_enrollments(
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_all_enrollments(db)


@router.get("/enrollments/employee/{employee_id}", response_model=list[EnrollmentOut])
async def enrollments_for_employee(
    employee_id: int,
    user: User = Depends(manager_only),
    db: Session = Depends(get_db),
):
    return get_enrollments_by_employee(employee_id, db)


@router.post("/enrollments/create", response_model=EnrollmentOut)
async def add_enrollment(
    data: EnrollmentCreate,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return create_enrollment(data, db)


@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentOut)
async def edit_enrollment(
    enrollment_id: int,
    data: EnrollmentUpdate,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return update_enrollment(enrollment_id, data, db)


@router.delete("/enrollments/{enrollment_id}")
async def remove_enrollment(
    enrollment_id: int,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return delete_enrollment(enrollment_id, db)
