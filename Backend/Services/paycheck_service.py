from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.Paychecks import Paychecks
from Backend.Models.Employee import Employee
from Backend.Models.User import User
from Backend.Models.pay_periods import PayPeriods
from Backend.Models.employee_position import EmployeePosition
from Backend.Models.Tax_information import TaxInformation
from Backend.Models.Time_entries import TimeEntries
from Backend.Models.Department import Department
from Backend.Models.Positions import Positions
from Backend.Schemas.Paycheck import PaycheckCreate, PaycheckStatusUpdate
import random, string

FEDERAL_BRACKETS = [(503,0.10),(1600,0.12),(3083,0.22),(5983,0.24),(7358,0.32),(9183,0.35),(float('inf'),0.37)]
SOCIAL_SECURITY_RATE = 0.062
MEDICARE_RATE = 0.0145
STATE_TAX_RATE = 0.05

def _generate_check_number():
    return 'CHK-' + ''.join(random.choices(string.digits, k=8))

def _calc_federal_tax(taxable, allowances):
    adjusted = max(0.0, taxable - allowances * 175.0)
    tax, prev = 0.0, 0.0
    for bracket, rate in FEDERAL_BRACKETS:
        if adjusted <= prev: break
        tax += (min(adjusted, bracket) - prev) * rate
        prev = bracket
    return round(tax, 2)

def get_all_paychecks(db: Session):
    return db.query(Paychecks).all()

def calculate_paycheck(employee_id: int, pay_period_id: int, db: Session):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee: raise HTTPException(status_code=404, detail='Employee not found')
    pay_period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not pay_period: raise HTTPException(status_code=404, detail='Pay period not found')
    emp_pos = db.query(EmployeePosition).filter(EmployeePosition.employee_id == employee_id, EmployeePosition.is_current == True).first()

    # Get the associated position for fallback rates
    position = None
    if emp_pos:
        position = db.query(Positions).filter(Positions.position_id == emp_pos.position_id).first()

    time_entries = db.query(TimeEntries).filter(TimeEntries.employee_id == employee_id, TimeEntries.entry_date >= pay_period.period_start_date, TimeEntries.entry_date <= pay_period.period_end_date).all()
    regular_hours = sum(float(e.regular_hours or 0) for e in time_entries)
    overtime_hours = sum(float(e.overtime_hours or 0) for e in time_entries)

    # Try employee position rates first, then fall back to position table rates
    hourly = None
    salary = None
    pay_freq = emp_pos.pay_frequency if emp_pos else 'bi_weekly'

    if emp_pos and float(emp_pos.current_hourly_rate or 0) > 0:
        hourly = float(emp_pos.current_hourly_rate)
    elif position and float(position.hourly_rate or 0) > 0:
        hourly = float(position.hourly_rate)
        pay_freq = emp_pos.pay_frequency if emp_pos else 'bi_weekly'

    if emp_pos and float(emp_pos.current_salary or 0) > 0:
        salary = float(emp_pos.current_salary)
    elif position and float(position.base_salary or 0) > 0:
        salary = float(position.base_salary)
        pay_freq = emp_pos.pay_frequency if emp_pos else 'bi_weekly'

    # Calculate gross pay based on available rates
    if hourly is not None:
        gross_pay = (regular_hours * hourly) + (overtime_hours * hourly * 1.5)
    elif salary is not None:
        freq_map = {'weekly': 52, 'bi_weekly': 26, 'semi_monthly': 24, 'monthly': 12}
        gross_pay = salary / freq_map.get(pay_freq, 26)
    else:
        gross_pay = 0.0

    gross_pay = round(gross_pay, 2)
    tax_info = db.query(TaxInformation).filter(TaxInformation.employee_id == employee_id).order_by(TaxInformation.effective_date.desc()).first()
    fed_allow = int(tax_info.federal_allowances) if tax_info else 0
    federal_tax = 0.0 if (tax_info and tax_info.exempt_federal) else _calc_federal_tax(gross_pay, fed_allow)
    state_tax = 0.0 if (tax_info and tax_info.exempt_state) else round(gross_pay * STATE_TAX_RATE, 2)
    social_security = round(gross_pay * SOCIAL_SECURITY_RATE, 2)
    medicare = round(gross_pay * MEDICARE_RATE, 2)
    net_pay = round(gross_pay - (federal_tax + state_tax + social_security + medicare), 2)
    return {'employee_id': employee_id, 'pay_period_id': pay_period_id, 'gross_pay': gross_pay, 'net_pay': net_pay, 'federal_tax': federal_tax, 'state_tax': state_tax, 'social_security': social_security, 'medicare': medicare, 'health_insurance': 0.0, 'retirement_401k': 0.0, 'other_deductions': 0.0}

def create_paycheck(data: PaycheckCreate, db: Session):
    existing = db.query(Paychecks).filter(Paychecks.employee_id == data.employee_id, Paychecks.pay_period_id == data.pay_period_id).first()
    if existing: raise HTTPException(status_code=409, detail='Paycheck already exists for this employee and pay period')
    paycheck = Paychecks(employee_id=data.employee_id, pay_period_id=data.pay_period_id, check_number=data.check_number or _generate_check_number(), gross_pay=data.gross_pay, net_pay=data.net_pay, federal_tax=data.federal_tax, state_tax=data.state_tax, social_security=data.social_security, medicare=data.medicare, health_insurance=data.health_insurance, retirement_401k=data.retirement_401k, other_deductions=data.other_deductions, payment_method=data.payment_method, payment_status=data.payment_status, payment_date=data.payment_date)
    db.add(paycheck); db.commit(); db.refresh(paycheck)
    return paycheck

def get_paychecks_by_employee(employee_id: int, db: Session):
    if not db.query(Employee).filter(Employee.employee_id == employee_id).first(): raise HTTPException(status_code=404, detail='Employee not found')
    return db.query(Paychecks).filter(Paychecks.employee_id == employee_id).all()

def get_paychecks_by_period(pay_period_id: int, db: Session):
    if not db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first(): raise HTTPException(status_code=404, detail='Pay period not found')
    return db.query(Paychecks).filter(Paychecks.pay_period_id == pay_period_id).all()


def get_paychecks_for_employee_ids(employee_ids: list[int], db: Session):
    if not employee_ids:
        return []
    return db.query(Paychecks).filter(Paychecks.employee_id.in_(employee_ids)).order_by(Paychecks.pay_period_id.desc(), Paychecks.paycheck_id.desc()).all()


def get_paychecks_for_employee_ids_by_period(employee_ids: list[int], pay_period_id: int, db: Session):
    if not employee_ids:
        return []
    return db.query(Paychecks).filter(Paychecks.employee_id.in_(employee_ids), Paychecks.pay_period_id == pay_period_id).all()


def get_all_pay_periods(db: Session):
    return db.query(PayPeriods).order_by(PayPeriods.period_start_date.desc()).all()


def _get_managed_department_ids_for_user(user: User, db: Session) -> list[int]:
    # First try: user is linked to an employee record
    manager_employee = db.query(Employee).filter(Employee.user_id == user.user_id).first()
    if manager_employee:
        return _get_managed_department_ids(manager_employee.employee_id, db)

    # Second try: find departments where manager_user_id matches this user's id
    managed_depts = db.query(Department).filter(Department.manager_user_id == user.user_id).all()
    if managed_depts:
        return [d.department_id for d in managed_depts]

    return []


def get_managed_employee_ids_for_user(user: User, db: Session) -> list[int]:
    dept_ids = _get_managed_department_ids_for_user(user, db)
    if not dept_ids:
        return []

    direct_employee_ids = {
        employee_id
        for (employee_id,) in db.query(Employee.employee_id)
        .filter(
            Employee.department_id.in_(dept_ids),
            Employee.employment_status == 'active'
        )
        .all()
    }

    position_employee_ids = {
        employee_id
        for (employee_id,) in db.query(Employee.employee_id)
        .join(EmployeePosition, EmployeePosition.employee_id == Employee.employee_id)
        .join(Positions, Positions.position_id == EmployeePosition.position_id)
        .filter(
            Positions.department_id.in_(dept_ids),
            EmployeePosition.is_current == True,
            Employee.employment_status == 'active'
        )
        .all()
    }

    return sorted(direct_employee_ids | position_employee_ids)


def _get_managed_department_ids(manager_employee_id: int, db: Session) -> list[int]:
    return [
        department.department_id
        for department in db.query(Department).filter(Department.manager_id == manager_employee_id).all()
    ]


def get_managed_employee_ids(manager_employee_id: int, db: Session) -> list[int]:
    dept_ids = _get_managed_department_ids(manager_employee_id, db)
    if not dept_ids:
        return []

    direct_employee_ids = {
        employee_id
        for (employee_id,) in db.query(Employee.employee_id)
        .filter(
            Employee.department_id.in_(dept_ids),
            Employee.employment_status == 'active'
        )
        .all()
    }

    position_employee_ids = {
        employee_id
        for (employee_id,) in db.query(Employee.employee_id)
        .join(EmployeePosition, EmployeePosition.employee_id == Employee.employee_id)
        .join(Positions, Positions.position_id == EmployeePosition.position_id)
        .filter(
            Positions.department_id.in_(dept_ids),
            EmployeePosition.is_current == True,
            Employee.employment_status == 'active'
        )
        .all()
    }

    return sorted(direct_employee_ids | position_employee_ids)


def run_payroll(pay_period_id: int, db: Session, employee_ids: list[int] | None = None):
    pay_period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not pay_period: raise HTTPException(status_code=404, detail='Pay period not found')
    if pay_period.status not in ('open', 'processing'): raise HTTPException(status_code=400, detail=f'Pay period is not open')

    employees_query = db.query(Employee).filter(Employee.employment_status == 'active')
    if employee_ids is not None:
        employees = employees_query.filter(Employee.employee_id.in_(employee_ids)).all() if employee_ids else []
    else:
        employees = employees_query.all()

    created = []
    for emp in employees:
        if db.query(Paychecks).filter(Paychecks.employee_id == emp.employee_id, Paychecks.pay_period_id == pay_period_id).first():
            continue
        amounts = calculate_paycheck(emp.employee_id, pay_period_id, db)
        if amounts['gross_pay'] == 0.0:
            continue
        p = Paychecks(
            employee_id=emp.employee_id,
            pay_period_id=pay_period_id,
            check_number=_generate_check_number(),
            payment_method='direct deposit',
            payment_status='processed',
            payment_date=pay_period.pay_date,
            gross_pay=amounts['gross_pay'],
            net_pay=amounts['net_pay'],
            federal_tax=amounts['federal_tax'],
            state_tax=amounts['state_tax'],
            social_security=amounts['social_security'],
            medicare=amounts['medicare'],
            health_insurance=amounts['health_insurance'],
            retirement_401k=amounts['retirement_401k'],
            other_deductions=amounts['other_deductions'],
        )
        db.add(p)
        created.append(p)
    pay_period.status = 'processing'
    db.commit()
    for p in created:
        db.refresh(p)
    return {'paychecks_created': len(created), 'pay_period_id': pay_period_id}


def get_paychecks_for_manager(manager_employee_id: int, db: Session):
    emp_ids = get_managed_employee_ids(manager_employee_id, db)
    if not emp_ids:
        return []
    return db.query(Paychecks).filter(
        Paychecks.employee_id.in_(emp_ids)
    ).order_by(Paychecks.pay_period_id.desc(), Paychecks.paycheck_id.desc()).all()


def get_paychecks_for_manager_by_period(manager_employee_id: int, pay_period_id: int, db: Session):
    emp_ids = get_managed_employee_ids(manager_employee_id, db)
    if not emp_ids:
        return []
    return db.query(Paychecks).filter(
        Paychecks.employee_id.in_(emp_ids),
        Paychecks.pay_period_id == pay_period_id
    ).all()

def update_paycheck_status(paycheck_id: int, data: PaycheckStatusUpdate, db: Session):
    paycheck = db.query(Paychecks).filter(Paychecks.paycheck_id == paycheck_id).first()
    if not paycheck: raise HTTPException(status_code=404, detail='Paycheck not found')
    paycheck.payment_status = data.payment_status
    if data.payment_date: paycheck.payment_date = data.payment_date
    db.commit(); db.refresh(paycheck)
    return paycheck
