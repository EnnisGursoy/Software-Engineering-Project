from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, hr_only, manager_or_hr_read, get_current_employee
from Backend.Models.Employee import Employee
from Backend.Models.User import User
from Backend.Schemas.TaxInformation import TaxInfoCreate, TaxInfoOut, TaxInfoUpdate
from Backend.Services.taxinfo_service import (
    create_tax_info,
    get_tax_info_by_employee,
    get_all_tax_info,
    update_tax_info,
    delete_tax_info,
)

router = APIRouter()


@router.get("/me", response_model=list[TaxInfoOut])
async def my_tax_info(
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    return get_tax_info_by_employee(employee.employee_id, db)


@router.get("/all", response_model=list[TaxInfoOut])
@router.get("/", response_model=list[TaxInfoOut])
async def list_all(
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return get_all_tax_info(db)


@router.get("/employee/{employee_id}", response_model=list[TaxInfoOut])
async def get_by_employee(
    employee_id: int,
    user: User = Depends(manager_or_hr_read),
    db: Session = Depends(get_db),
):
    return get_tax_info_by_employee(employee_id, db)


@router.post("/create", response_model=TaxInfoOut)
async def create(
    data: TaxInfoCreate,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return create_tax_info(data, db)


@router.patch("/{tax_id}", response_model=TaxInfoOut)
async def update(
    tax_id: int,
    data: TaxInfoUpdate,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return update_tax_info(tax_id, data, db)


@router.delete("/{tax_id}")
async def delete(
    tax_id: int,
    user: User = Depends(hr_only),
    db: Session = Depends(get_db),
):
    return delete_tax_info(tax_id, db)
