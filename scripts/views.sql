-- =====================================================
-- Payroll System - Views
-- Pre-built queries for reporting and quick lookups
-- =====================================================

USE payroll_system;

-- -----------------------------------------------------
-- View: vw_employee_directory
-- Complete employee listing with current position,
-- department, and pay information
-- -----------------------------------------------------
DROP VIEW IF EXISTS vw_employee_directory;
CREATE VIEW vw_employee_directory AS
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
    ep.pay_frequency,
    ep.start_date AS position_start_date
FROM employees e
LEFT JOIN employee_positions ep ON e.employee_id = ep.employee_id AND ep.is_current = 1
LEFT JOIN positions p ON ep.position_id = p.position_id
LEFT JOIN departments d ON p.department_id = d.department_id;

-- -----------------------------------------------------
-- View: vw_active_employees
-- Only active employees with their current assignments
-- -----------------------------------------------------
DROP VIEW IF EXISTS vw_active_employees;
CREATE VIEW vw_active_employees AS
SELECT *
FROM vw_employee_directory
WHERE employment_status = 'active';

-- -----------------------------------------------------
-- View: vw_payroll_summary
-- Paycheck details with employee names and period info
-- -----------------------------------------------------
DROP VIEW IF EXISTS vw_payroll_summary;
CREATE VIEW vw_payroll_summary AS
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
LEFT JOIN departments d ON p.department_id = d.department_id;

-- -----------------------------------------------------
-- View: vw_department_costs
-- Total salary and headcount costs per department
-- -----------------------------------------------------
DROP VIEW IF EXISTS vw_department_costs;
CREATE VIEW vw_department_costs AS
SELECT
    d.department_id,
    d.department_name,
    COUNT(DISTINCT e.employee_id) AS headcount,
    SUM(CASE WHEN ep.current_salary IS NOT NULL THEN ep.current_salary ELSE 0 END) AS total_annual_salaries,
    COUNT(CASE WHEN ep.current_hourly_rate IS NOT NULL THEN 1 END) AS hourly_employees,
    COUNT(CASE WHEN ep.current_salary IS NOT NULL THEN 1 END) AS salaried_employees,
    ROUND(AVG(CASE WHEN ep.current_salary IS NOT NULL THEN ep.current_salary END), 2) AS avg_salary
FROM departments d
LEFT JOIN positions p ON d.department_id = p.department_id
LEFT JOIN employee_positions ep ON p.position_id = ep.position_id AND ep.is_current = 1
LEFT JOIN employees e ON ep.employee_id = e.employee_id AND e.employment_status = 'active'
GROUP BY d.department_id, d.department_name;

-- -----------------------------------------------------
-- View: vw_time_entry_report
-- Time entries with employee names and weekly totals
-- -----------------------------------------------------
DROP VIEW IF EXISTS vw_time_entry_report;
CREATE VIEW vw_time_entry_report AS
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
    te.approved,
    CASE WHEN te.approved = 1 THEN 'Approved' ELSE 'Pending' END AS approval_status,
    CONCAT(a.first_name, ' ', a.last_name) AS approved_by_name
FROM time_entries te
JOIN employees e ON te.employee_id = e.employee_id
LEFT JOIN employee_positions ep ON e.employee_id = ep.employee_id AND ep.is_current = 1
LEFT JOIN positions p ON ep.position_id = p.position_id
LEFT JOIN departments d ON p.department_id = d.department_id
LEFT JOIN employees a ON te.approved_by = a.employee_id;

-- -----------------------------------------------------
-- View: vw_employee_pay_history
-- Historical paycheck records per employee
-- -----------------------------------------------------
DROP VIEW IF EXISTS vw_employee_pay_history;
CREATE VIEW vw_employee_pay_history AS
SELECT
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    pp.period_start_date,
    pp.period_end_date,
    pc.gross_pay,
    pc.net_pay,
    (pc.federal_tax + pc.state_tax + pc.social_security + pc.medicare) AS total_taxes,
    (pc.health_insurance + pc.retirement_401k + pc.other_deductions) AS total_deductions,
    pc.payment_status,
    pc.payment_date,
    pc.check_number
FROM employees e
JOIN paychecks pc ON e.employee_id = pc.employee_id
JOIN pay_periods pp ON pc.pay_period_id = pp.pay_period_id
ORDER BY e.employee_id, pp.period_start_date DESC;

-- -----------------------------------------------------
-- View: vw_pay_period_summary
-- Summary totals for each pay period
-- -----------------------------------------------------
DROP VIEW IF EXISTS vw_pay_period_summary;
CREATE VIEW vw_pay_period_summary AS
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
    COALESCE(SUM(pc.federal_tax + pc.state_tax + pc.social_security + pc.medicare), 0) AS total_taxes,
    COALESCE(SUM(pc.health_insurance + pc.retirement_401k + pc.other_deductions), 0) AS total_deductions
FROM pay_periods pp
LEFT JOIN paychecks pc ON pp.pay_period_id = pc.pay_period_id AND pc.payment_status != 'void'
GROUP BY pp.pay_period_id, pp.period_start_date, pp.period_end_date,
         pp.pay_date, pp.period_type, pp.status;

-- -----------------------------------------------------
-- View: vw_employee_tax_summary
-- Employee tax information with filing details
-- -----------------------------------------------------
DROP VIEW IF EXISTS vw_employee_tax_summary;
CREATE VIEW vw_employee_tax_summary AS
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
ORDER BY e.last_name, e.first_name;
