-- =====================================================
-- Payroll System - Indexes
-- Performance optimization for common queries
-- =====================================================

USE payroll_system;

-- =====================================================
-- employees table
-- =====================================================

-- Fast lookup by employment status (filtering active/terminated)
CREATE INDEX idx_employees_status
    ON employees (employment_status);

-- Searching employees by name
CREATE INDEX idx_employees_name
    ON employees (last_name, first_name);

-- Lookup by hire date (reporting, anniversary queries)
CREATE INDEX idx_employees_hire_date
    ON employees (hire_date);

-- =====================================================
-- time_entries table
-- =====================================================

-- Fast lookup by employee and date range (payroll calculation)
CREATE INDEX idx_time_entries_emp_date
    ON time_entries (employee_id, entry_date);

-- Filtering by approval status
CREATE INDEX idx_time_entries_approved
    ON time_entries (approved);

-- Filtering by entry type (sick, vacation reports)
CREATE INDEX idx_time_entries_type
    ON time_entries (entry_type);

-- =====================================================
-- paychecks table
-- =====================================================

-- Lookup paychecks by status (pending processing)
CREATE INDEX idx_paychecks_status
    ON paychecks (payment_status);

-- Lookup by payment date (reporting)
CREATE INDEX idx_paychecks_payment_date
    ON paychecks (payment_date);

-- Composite: employee + status (employee pay history)
CREATE INDEX idx_paychecks_emp_status
    ON paychecks (employee_id, payment_status);

-- =====================================================
-- pay_periods table
-- =====================================================

-- Lookup by status (finding open pay periods)
CREATE INDEX idx_pay_periods_status
    ON pay_periods (status);

-- Lookup by date range
CREATE INDEX idx_pay_periods_dates
    ON pay_periods (period_start_date, period_end_date);

-- =====================================================
-- employee_positions table
-- =====================================================

-- Fast lookup for current positions
CREATE INDEX idx_emp_positions_current
    ON employee_positions (employee_id, is_current);

-- =====================================================
-- tax_information table
-- =====================================================

-- Lookup latest tax info by employee and effective date
CREATE INDEX idx_tax_info_emp_date
    ON tax_information (employee_id, effective_date);
