"""
Payroll Operations
Core business operations: generating paychecks, processing pay periods,
hiring employees, terminating employees, and voiding paychecks.
"""

from datetime import date
from db_connection import get_connection, execute_query
from payroll_functions import (
    calculate_employee_gross_pay,
    calculate_federal_tax,
    calculate_state_tax,
    calculate_social_security,
    calculate_medicare,
    get_ytd_gross,
    get_pay_periods_per_year,
)


def generate_paycheck(employee_id, pay_period_id):
    """
    Creates a paycheck for a single employee in a pay period.
    Calculates gross pay, all taxes/deductions, and net pay.
    Returns the new paycheck_id.
    """
    # Verify employee is active
    emp = execute_query(
        "SELECT employment_status, state FROM employees WHERE employee_id = %s",
        (employee_id,),
        fetch=True,
    )
    if not emp:
        raise ValueError(f"Employee {employee_id} not found")
    if emp[0]["employment_status"] != "active":
        raise ValueError(f"Employee {employee_id} is not active")

    emp_state = emp[0]["state"]

    # Check for duplicate paycheck
    existing = execute_query(
        """SELECT paycheck_id FROM paychecks
           WHERE employee_id = %s AND pay_period_id = %s AND payment_status != 'void'""",
        (employee_id, pay_period_id),
        fetch=True,
    )
    if existing:
        raise ValueError(f"Paycheck already exists for employee {employee_id} in pay period {pay_period_id}")

    # Get pay period info
    period = execute_query(
        "SELECT period_start_date, period_end_date, pay_date FROM pay_periods WHERE pay_period_id = %s",
        (pay_period_id,),
        fetch=True,
    )
    if not period:
        raise ValueError(f"Pay period {pay_period_id} not found")

    period_start = period[0]["period_start_date"]
    period_end = period[0]["period_end_date"]
    pay_date = period[0]["pay_date"]

    # Get tax information
    tax_info = execute_query(
        """SELECT filing_status, federal_allowances, state_allowances,
                  additional_withholding, exempt_federal, exempt_state
           FROM tax_information
           WHERE employee_id = %s
           ORDER BY effective_date DESC LIMIT 1""",
        (employee_id,),
        fetch=True,
    )
    if not tax_info:
        raise ValueError(f"No tax information found for employee {employee_id}")

    ti = tax_info[0]

    # Get pay frequency
    position = execute_query(
        "SELECT pay_frequency FROM employee_positions WHERE employee_id = %s AND is_current = 1 LIMIT 1",
        (employee_id,),
        fetch=True,
    )
    if not position:
        raise ValueError(f"No active position found for employee {employee_id}")

    pay_frequency = position[0]["pay_frequency"]

    # Calculate gross pay
    gross_pay = calculate_employee_gross_pay(employee_id, period_start, period_end)
    if gross_pay <= 0:
        raise ValueError(f"Gross pay is zero for employee {employee_id}. Check time entries or position.")

    # Get YTD gross for SS/Medicare
    ytd_gross = get_ytd_gross(employee_id, period_start.year)

    # Calculate taxes
    federal_tax = calculate_federal_tax(
        gross_pay, pay_frequency, ti["filing_status"],
        ti["federal_allowances"], ti["additional_withholding"], ti["exempt_federal"],
    )
    state_tax = calculate_state_tax(
        gross_pay, emp_state, ti["state_allowances"], ti["exempt_state"],
    )
    ss_tax = calculate_social_security(gross_pay, ytd_gross)
    medicare_tax = calculate_medicare(gross_pay, ytd_gross)

    # Net pay
    net_pay = gross_pay - federal_tax - state_tax - ss_tax - medicare_tax

    # Generate check number
    check_number = f"{pay_date.strftime('%Y%m%d')}-{employee_id:04d}-{pay_period_id:04d}"

    # Insert paycheck
    paycheck_id = execute_query(
        """INSERT INTO paychecks
           (employee_id, pay_period_id, check_number, gross_pay, net_pay,
            federal_tax, state_tax, social_security, medicare,
            health_insurance, retirement_401k, other_deductions,
            payment_method, payment_status, payment_date)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, 0, 'direct_deposit', 'pending', %s)""",
        (employee_id, pay_period_id, check_number,
         float(gross_pay), float(net_pay),
         float(federal_tax), float(state_tax), float(ss_tax), float(medicare_tax),
         pay_date),
    )

    return paycheck_id


def process_pay_period(pay_period_id):
    """
    Processes an entire pay period: generates paychecks for all active employees.
    Returns a dict with success count, errors, and details.
    """
    # Verify pay period is open
    period = execute_query(
        "SELECT status FROM pay_periods WHERE pay_period_id = %s",
        (pay_period_id,),
        fetch=True,
    )
    if not period:
        raise ValueError(f"Pay period {pay_period_id} not found")
    if period[0]["status"] != "open":
        raise ValueError(f"Pay period is not open (current status: {period[0]['status']})")

    # Set to processing
    execute_query(
        "UPDATE pay_periods SET status = 'processing' WHERE pay_period_id = %s",
        (pay_period_id,),
    )

    # Get all active employees with current positions
    employees = execute_query(
        """SELECT DISTINCT e.employee_id
           FROM employees e
           JOIN employee_positions ep ON e.employee_id = ep.employee_id
           WHERE e.employment_status = 'active' AND ep.is_current = 1""",
        fetch=True,
    )

    success_count = 0
    errors = []

    for emp in employees:
        try:
            generate_paycheck(emp["employee_id"], pay_period_id)
            success_count += 1
        except Exception as e:
            errors.append({"employee_id": emp["employee_id"], "error": str(e)})

    # Update status
    if success_count > 0 and not errors:
        execute_query(
            "UPDATE pay_periods SET status = 'paid' WHERE pay_period_id = %s",
            (pay_period_id,),
        )
    elif success_count > 0:
        # Partial success — keep as processing so it can be reviewed
        pass
    else:
        # All failed — revert to open
        execute_query(
            "UPDATE pay_periods SET status = 'open' WHERE pay_period_id = %s",
            (pay_period_id,),
        )

    return {
        "pay_period_id": pay_period_id,
        "paychecks_generated": success_count,
        "errors": errors,
    }


def add_employee(first_name, last_name, email, phone, address, city, state,
                 zip_code, date_of_birth, hire_date, ssn, position_id,
                 salary, hourly_rate, pay_frequency,
                 filing_status, federal_allowances=0, state_allowances=0):
    """
    Adds a new employee with position assignment and tax information
    in a single transaction.
    Returns the new employee_id.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert employee
        cursor.execute(
            """INSERT INTO employees
               (first_name, last_name, email, phone, address, city, state,
                zip_code, date_of_birth, hire_date, ssn, employment_status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')""",
            (first_name, last_name, email, phone, address, city, state,
             zip_code, date_of_birth, hire_date, ssn),
        )
        employee_id = cursor.lastrowid

        # Assign position
        cursor.execute(
            """INSERT INTO employee_positions
               (employee_id, position_id, start_date, current_salary,
                current_hourly_rate, pay_frequency, is_current)
               VALUES (%s, %s, %s, %s, %s, %s, 1)""",
            (employee_id, position_id, hire_date, salary, hourly_rate, pay_frequency),
        )

        # Add tax information
        cursor.execute(
            """INSERT INTO tax_information
               (employee_id, filing_status, federal_allowances,
                state_allowances, effective_date)
               VALUES (%s, %s, %s, %s, %s)""",
            (employee_id, filing_status, federal_allowances,
             state_allowances, hire_date),
        )

        conn.commit()
        return employee_id

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def terminate_employee(employee_id, termination_date=None):
    """
    Terminates an employee: updates status, sets termination date,
    and closes current position assignments.
    """
    if termination_date is None:
        termination_date = date.today()

    emp = execute_query(
        "SELECT employment_status FROM employees WHERE employee_id = %s",
        (employee_id,),
        fetch=True,
    )
    if not emp:
        raise ValueError(f"Employee {employee_id} not found")
    if emp[0]["employment_status"] == "terminated":
        raise ValueError(f"Employee {employee_id} is already terminated")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """UPDATE employees
               SET employment_status = 'terminated', termination_date = %s
               WHERE employee_id = %s""",
            (termination_date, employee_id),
        )

        cursor.execute(
            """UPDATE employee_positions
               SET is_current = 0, end_date = %s
               WHERE employee_id = %s AND is_current = 1""",
            (termination_date, employee_id),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def void_paycheck(paycheck_id, reason=""):
    """Voids a paycheck by setting its status to 'void'."""
    check = execute_query(
        "SELECT payment_status FROM paychecks WHERE paycheck_id = %s",
        (paycheck_id,),
        fetch=True,
    )
    if not check:
        raise ValueError(f"Paycheck {paycheck_id} not found")
    if check[0]["payment_status"] == "void":
        raise ValueError(f"Paycheck {paycheck_id} is already voided")

    execute_query(
        "UPDATE paychecks SET payment_status = 'void' WHERE paycheck_id = %s",
        (paycheck_id,),
    )

    return {"paycheck_id": paycheck_id, "status": "voided", "reason": reason}
