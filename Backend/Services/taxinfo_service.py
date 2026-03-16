from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.Tax_information import TaxInformation
from Backend.Models.Employee import Employee
from Backend.Schemas.TaxInformation import TaxInfoCreate, TaxInfoUpdate

VALID_FILING_STATUSES = {"single", "married", "head_of_household"}


def create_tax_info(data: TaxInfoCreate, db: Session):
    if data.filing_status not in VALID_FILING_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid filing status. Choose from: {VALID_FILING_STATUSES}")

    employee = db.query(Employee).filter(Employee.employee_id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    record = TaxInformation(
        employee_id=data.employee_id,
        filing_status=data.filing_status,
        federal_allowances=data.federal_allowances,
        state_allowances=data.state_allowances,
        additional_withholding=data.additional_withholding,
        exempt_state=data.exempt_state,
        exempt_federal=data.exempt_federal,
        effective_date=data.effective_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_tax_info_by_employee(employee_id: int, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return (
        db.query(TaxInformation)
        .filter(TaxInformation.employee_id == employee_id)
        .order_by(TaxInformation.effective_date.desc())
        .all()
    )


def get_all_tax_info(db: Session):
    return db.query(TaxInformation).all()


def update_tax_info(tax_id: int, data: TaxInfoUpdate, db: Session):
    record = db.query(TaxInformation).filter(TaxInformation.tax_id == tax_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Tax information record not found")

    if data.filing_status and data.filing_status not in VALID_FILING_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid filing status. Choose from: {VALID_FILING_STATUSES}")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


def delete_tax_info(tax_id: int, db: Session):
    record = db.query(TaxInformation).filter(TaxInformation.tax_id == tax_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Tax information record not found")
    db.delete(record)
    db.commit()
    return {"message": "Tax information deleted"}
