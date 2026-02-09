"""
Payroll Views (Reporting Queries)
Functions that return formatted data for reports and dashboards.
These replace SQL views with callable Python functions.
"""

from db_connection import execute_query


def get_employee_directory(status_filter=None):
    """
    Returns all employees with their current position, department, and pay info.
    Optionally filter by employment status ('active', 'terminated', 'on_leave').
    """
    query = """
        SELECT
            e.employee_id,
            CONCAT(e.first_name, ' ', e.last_name) AS full_name,
            e.email,
            e.phone,
            CONCAT(e.address, ', ', e.city, ', ', e.state, ' ', e.zip_code) AS full_address,
            e.hire_date,
            e.termination_date,
            e.employment_status,
            p.position_title,
            d.department_name,
            p.employment_type,
            ep.current_salary,
            ep.current_hourly_rate,
            ep.pay_frequency
        FROM employees e
        LEFT JOIN employee_positions ep ON e.employee_id = ep.employee_id AND ep.is_current = 1
        LEFT JOIN positions p ON ep.position_id = p.position_id
        LEFT JOIN departments d ON p.department_id = d.department_id
    """
    params = ()

    if status_filter:
        query += " WHERE e.employment_status = %s"
        params = (status_filter,)

    query += " ORDER BY e.last_name, e.first_name"
    return execute_query(query, params, fetch=True)


def get_active_employees():
    """Returns only active employees with their current assignments."""
    return get_employee_directory(status_filter="active")


def get_payroll_summary(pay_period_id=None):
    """
    Returns paycheck details with employee names and period info.
    Optionally filter by a specific pay period.
    """
    query = """
        SELECT
            pc.paycheck_id,
            pc.check_number,
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            d.department_name,
            pp.period_start_date,
            pp.period_end_date,
            pp.pay_date,
            pc.gross_pay,
            pc.federal_tax,
            pc.state_tax,
            pc.social_security,
            pc.medicare,
            (pc.federal_tax + pc.state_tax + pc.social_security + pc.medicare) AS total_taxes,
            pc.health_insurance,
            pc.retirement_401k,
            pc.other_deductions,
            (pc.health_insurance + pc.retirement_401k + pc.other_deductions) AS total_benefits,
            pc.net_pay,
            pc.payment_method,
            pc.payment_status
        FROM paychecks pc
        JOIN employees e ON pc.employee_id = e.employee_id
        JOIN pay_periods pp ON pc.pay_period_id = pp.pay_period_id
        LEFT JOIN employee_positions ep ON e.employee_id = ep.employee_id AND ep.is_current = 1
        LEFT JOIN positions p ON ep.position_id = p.position_id
        LEFT JOIN departments d ON p.department_id = d.department_id
        WHERE pc.payment_status != 'void'
    """
    params = ()

    if pay_period_id:
        query += " AND pc.pay_period_id = %s"
        params = (pay_period_id,)

    query += " ORDER BY e.last_name, e.first_name"
    return execute_query(query, params, fetch=True)


def get_department_costs():
    """
    Returns salary totals and headcount per department.
    Only counts active employees.
    """
    return execute_query(
        """
        SELECT
            d.department_id,
            d.department_name,
            COUNT(DISTINCT e.employee_id) AS headcount,
            COALESCE(SUM(ep.current_salary), 0) AS total_annual_salaries,
            COUNT(CASE WHEN ep.current_hourly_rate IS NOT NULL THEN 1 END) AS hourly_employees,
            COUNT(CASE WHEN ep.current_salary IS NOT NULL THEN 1 END) AS salaried_employees,
            ROUND(AVG(ep.current_salary), 2) AS avg_salary
        FROM departments d
        LEFT JOIN positions p ON d.department_id = p.department_id
        LEFT JOIN employee_positions ep ON p.position_id = ep.position_id AND ep.is_current = 1
        LEFT JOIN employees e ON ep.employee_id = e.employee_id AND e.employment_status = 'active'
        GROUP BY d.department_id, d.department_name
        ORDER BY d.department_name
        """,
        fetch=True,
    )


def get_time_entries(employee_id=None, start_date=None, end_date=None, approved_only=False):
    """
    Returns time entries with employee names.
    Supports filtering by employee, date range, and approval status.
    """
    query = """
        SELECT
            te.entry_id,
            te.employee_id,
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            d.department_name,
            te.entry_date,
            DAYNAME(te.entry_date) AS day_of_week,
            te.clock_in,
            te.clock_out,
            te.regular_hours,
            te.overtime_hours,
            (te.regular_hours + te.overtime_hours) AS total_hours,
            te.entry_type,
            te.notes,
            CASE WHEN te.approved = 1 THEN 'Approved' ELSE 'Pending' END AS approval_status,
            CONCAT(a.first_name, ' ', a.last_name) AS approved_by_name
        FROM time_entries te
        JOIN employees e ON te.employee_id = e.employee_id
        LEFT JOIN employee_positions ep ON e.employee_id = ep.employee_id AND ep.is_current = 1
        LEFT JOIN positions p ON ep.position_id = p.position_id
        LEFT JOIN departments d ON p.department_id = d.department_id
        LEFT JOIN employees a ON te.approved_by = a.employee_id
        WHERE 1=1
    """
    params = []

    if employee_id:
        query += " AND te.employee_id = %s"
        params.append(employee_id)
    if start_date:
        query += " AND te.entry_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND te.entry_date <= %s"
        params.append(end_date)
    if approved_only:
        query += " AND te.approved = 1"

    query += " ORDER BY te.entry_date DESC, e.last_name"
    return execute_query(query, tuple(params), fetch=True)


def get_employee_pay_history(employee_id):
    """Returns all paycheck records for a specific employee, newest first."""
    return execute_query(
        """
        SELECT
            pp.period_start_date,
            pp.period_end_date,
            pc.gross_pay,
            pc.net_pay,
            (pc.federal_tax + pc.state_tax + pc.social_security + pc.medicare) AS total_taxes,
            (pc.health_insurance + pc.retirement_401k + pc.other_deductions) AS total_deductions,
            pc.payment_status,
            pc.payment_date,
            pc.check_number
        FROM paychecks pc
        JOIN pay_periods pp ON pc.pay_period_id = pp.pay_period_id
        WHERE pc.employee_id = %s
        ORDER BY pp.period_start_date DESC
        """,
        (employee_id,),
        fetch=True,
    )


def get_pay_period_summary():
    """Returns summary totals for each pay period."""
    return execute_query(
        """
        SELECT
            pp.pay_period_id,
            pp.period_start_date,
            pp.period_end_date,
            pp.pay_date,
            pp.period_type,
            pp.status,
            COUNT(pc.paycheck_id) AS total_paychecks,
            COALESCE(SUM(pc.gross_pay), 0) AS total_gross,
            COALESCE(SUM(pc.net_pay), 0) AS total_net,
            COALESCE(SUM(pc.federal_tax + pc.state_tax + pc.social_security + pc.medicare), 0) AS total_taxes
        FROM pay_periods pp
        LEFT JOIN paychecks pc ON pp.pay_period_id = pc.pay_period_id AND pc.payment_status != 'void'
        GROUP BY pp.pay_period_id, pp.period_start_date, pp.period_end_date,
                 pp.pay_date, pp.period_type, pp.status
        ORDER BY pp.period_start_date DESC
        """,
        fetch=True,
    )


def get_employee_tax_info():
    """Returns tax filing details for all active employees."""
    return execute_query(
        """
        SELECT
            e.employee_id,
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            e.state AS work_state,
            ti.filing_status,
            ti.federal_allowances,
            ti.state_allowances,
            ti.additional_withholding,
            CASE WHEN ti.exempt_federal = 1 THEN 'Yes' ELSE 'No' END AS federal_exempt,
            CASE WHEN ti.exempt_state = 1 THEN 'Yes' ELSE 'No' END AS state_exempt,
            ti.effective_date
        FROM employees e
        JOIN tax_information ti ON e.employee_id = ti.employee_id
        WHERE e.employment_status = 'active'
        ORDER BY e.last_name, e.first_name
        """,
        fetch=True,
    )
