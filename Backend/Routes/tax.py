from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from Backend.Utility.dependencies import get_db, get_current_user
from Backend.Models.User import User
from Backend.Schemas.Tax import TaxCreate, TaxUpdate, TaxOut
from Backend.Services.Tax_service import (
    create_tax, get_tax_by_employee, update_tax, delete_tax, list_all_tax
)
from Backend.Utility.dependencies import admin_only, hr_only

router = APIRouter(tags=["Tax Information"])


@router.get("/", response_model=list[TaxOut])
async def get_all_tax(db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return list_all_tax(db)


@router.post("/", response_model=TaxOut)
async def create_tax_info(data: TaxCreate, db: Session = Depends(get_db), user: User = Depends(hr_only)):
    return create_tax(data, db)


@router.get("/{employee_id}", response_model=TaxOut)
async def get_tax(employee_id: int, db: Session = Depends(get_db), user: User = Depends(hr_only)):
    return get_tax_by_employee(employee_id, db)


@router.patch("/{employee_id}", response_model=TaxOut)
async def update_tax_info(employee_id: int, data: TaxUpdate, db: Session = Depends(get_db), user: User = Depends(hr_only)):
    return update_tax(employee_id, data, db)


@router.delete("/{employee_id}")
async def delete_tax_info(employee_id: int, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return delete_tax(employee_id, db)
