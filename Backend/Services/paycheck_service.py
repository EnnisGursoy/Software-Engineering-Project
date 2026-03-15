from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.Paychecks import Paychecks
from Backend.Models.Employee import Employee
from Backend.Models.pay_periods import PayPeriods
from Backend.Models.employee_position import EmployeePosition
from Backend.Models.Tax_information import TaxInformation
from Backend.Models.Time_entries import TimeEntries
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
    time_entries = db.query(TimeEntries).filter(TimeEntries.employee_id == employee_id, TimeEntries.entry_date >= pay_period.period_start_date, TimeEntries.entry_date <= pay_period.period_end_date).all()
    regular_hours = sum(float(e.regular_hours or 0) for e in time_entries)
    overtime_hours = sum(float(e.overtime_hours or 0) for e in time_entries)
    if emp_pos and float(emp_pos.current_hourly_rate or 0) > 0:
        hourly = float(emp_pos.current_hourly_rate)
        gross_pay = (regular_hours * hourly) + (overtime_hours * hourly * 1.5)
    elif emp_pos and float(emp_pos.current_salary or 0) > 0:
        freq_map = {'weekly': 52, 'bi_weekly': 26, 'semi_monthly': 24, 'monthly': 12}
        gross_pay = float(emp_pos.current_salary) / freq_map.get(emp_pos.pay_frequency, 26)
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

def run_payroll(pay_period_id: int, db: Session):
    pay_period = db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first()
    if not pay_period: raise HTTPException(status_code=404, detail='Pay period not found')
    if pay_period.status not in ('open', 'processing'): raise HTTPException(status_code=400, detail=f'Pay period is not open')
    employees = db.query(Employee).filter(Employee.employment_status == 'active').all()
    created = []
    for emp in employees:
        if db.query(Paychecks).filter(Paychecks.employee_id == emp.employee_id, Paychecks.pay_period_id == pay_period_id).first(): continue
        amounts = calculate_paycheck(emp.employee_id, pay_period_id, db)
        if amounts['gross_pay'] == 0.0: continue
        p = Paychecks(employee_id=emp.employee_id, pay_period_id=pay_period_id, check_number=_generate_check_number(), payment_method='direct deposit', payment_status='processed', payment_date=pay_period.pay_date, gross_pay=amounts['gross_pay'], net_pay=amounts['net_pay'], federal_tax=amounts['federal_tax'], state_tax=amounts['state_tax'], social_security=amounts['social_security'], medicare=amounts['medicare'], health_insurance=amounts['health_insurance'], retirement_401k=amounts['retirement_401k'], other_deductions=amounts['other_deductions'])
        db.add(p); created.append(p)
    pay_period.status = 'processing'; db.commit()
    for p in created: db.refresh(p)
    return {'paychecks_created': len(created), 'pay_period_id': pay_period_id}

def get_paychecks_by_employee(employee_id: int, db: Session):
    if not db.query(Employee).filter(Employee.employee_id == employee_id).first(): raise HTTPException(status_code=404, detail='Employee not found')
    return db.query(Paychecks).filter(Paychecks.employee_id == employee_id).all()

def get_paychecks_by_period(pay_period_id: int, db: Session):
    if not db.query(PayPeriods).filter(PayPeriods.pay_period_id == pay_period_id).first(): raise HTTPException(status_code=404, detail='Pay period not found')
    return db.query(Paychecks).filter(Paychecks.pay_period_id == pay_period_id).all()

def get_all_pay_periods(db: Session):
    return db.query(PayPeriods).order_by(PayPeriods.period_start_date.desc()).all()

def update_paycheck_status(paycheck_id: int, data: PaycheckStatusUpdate, db: Session):
    paycheck = db.query(Paychecks).filter(Paychecks.paycheck_id == paycheck_id).first()
    if not paycheck: raise HTTPException(status_code=404, detail='Paycheck not found')
    paycheck.payment_status = data.payment_status
    if data.payment_date: paycheck.payment_date = data.payment_date
    db.commit(); db.refresh(paycheck)
    return paycheck
