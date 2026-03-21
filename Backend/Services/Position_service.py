from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.Positions import Positions
from Backend.Models.employee_position import EmployeePosition
from Backend.Models.Employee import Employee
from Backend.Schemas.Position import PositionCreate, PositionUpdate, EmployeePositionCreate

VALID_EMPLOYMENT_TYPES = {"full_time", "part_time", "contract"}
VALID_PAY_FREQUENCIES  = {"weekly", "bi_weekly", "semi_monthly", "monthly"}


def get_all_positions(db: Session):
    return db.query(Positions).all()


def get_position(position_id: int, db: Session):
    position = db.query(Positions).filter(Positions.position_id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


def create_position(data: PositionCreate, db: Session):
    if data.employment_type not in VALID_EMPLOYMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid employment type. Choose from: {VALID_EMPLOYMENT_TYPES}")

    position = Positions(
        position_title=data.position_title,
        department_id=data.department_id,
        base_salary=data.base_salary,
        hourly_rate=data.hourly_rate,
        employment_type=data.employment_type,
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


def update_position(position_id: int, data: PositionUpdate, db: Session):
    position = db.query(Positions).filter(Positions.position_id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    if data.employment_type and data.employment_type not in VALID_EMPLOYMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid employment type. Choose from: {VALID_EMPLOYMENT_TYPES}")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(position, key, value)

    db.commit()
    db.refresh(position)
    return position


def delete_position(position_id: int, db: Session):
    position = db.query(Positions).filter(Positions.position_id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    db.delete(position)
    db.commit()
    return {"message": "Position deleted"}


def assign_position_to_employee(data: EmployeePositionCreate, db: Session):
    if data.pay_frequency not in VALID_PAY_FREQUENCIES:
        raise HTTPException(status_code=400, detail=f"Invalid pay frequency. Choose from: {VALID_PAY_FREQUENCIES}")

    employee = db.query(Employee).filter(Employee.employee_id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    position = db.query(Positions).filter(Positions.position_id == data.position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Mark any current position as no longer current
    db.query(EmployeePosition).filter(
        EmployeePosition.employee_id == data.employee_id,
        EmployeePosition.is_current == True,
    ).update({"is_current": False})

    emp_position = EmployeePosition(
        employee_id=data.employee_id,
        position_id=data.position_id,
        start_date=data.start_date,
        current_salary=data.current_salary,
        current_hourly_rate=data.current_hourly_rate,
        pay_frequency=data.pay_frequency,
        is_current=True,
    )
    db.add(emp_position)
    db.commit()
    db.refresh(emp_position)
    return emp_position


def get_positions_by_employee(employee_id: int, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return (
        db.query(EmployeePosition)
        .filter(EmployeePosition.employee_id == employee_id)
        .order_by(EmployeePosition.is_current.desc())
        .all()
    )
