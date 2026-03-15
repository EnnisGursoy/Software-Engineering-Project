from fastapi import HTTPException
from sqlalchemy.orm import Session
from Backend.Models.Tax_information import TaxInformation
from Backend.Models.Employee import Employee


def create_tax(data, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    tax = TaxInformation(**data.model_dump())
    db.add(tax)
    db.commit()
    db.refresh(tax)
    return tax


def get_tax_by_employee(employee_id: int, db: Session):
    tax = db.query(TaxInformation).filter(TaxInformation.employee_id == employee_id).first()
    if not tax:
        raise HTTPException(status_code=404, detail="Tax information not found")
    return tax


def update_tax(employee_id: int, data, db: Session):
    tax = db.query(TaxInformation).filter(TaxInformation.employee_id == employee_id).first()
    if not tax:
        raise HTTPException(status_code=404, detail="Tax information not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tax, key, value)

    db.commit()
    db.refresh(tax)
    return tax


def delete_tax(employee_id: int, db: Session):
    tax = db.query(TaxInformation).filter(TaxInformation.employee_id == employee_id).first()
    if not tax:
        raise HTTPException(status_code=404, detail="Tax information not found")

    db.delete(tax)
    db.commit()
    return {"message": "Tax information deleted successfully"}


def list_all_tax(db: Session):
    return db.query(TaxInformation).all()