-- =====================================================
-- Payroll System - Functions
-- Reusable calculations for tax, gross pay, and more
-- =====================================================

USE payroll_system;

DELIMITER //

-- -----------------------------------------------------
-- Function: calculate_social_security
-- Calculates Social Security tax (6.2% up to wage base)
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS calculate_social_security //
CREATE FUNCTION calculate_social_security(
    p_gross_pay DECIMAL(10,2),
    p_ytd_gross DECIMAL(12,2)
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_wage_base DECIMAL(12,2) DEFAULT 168600.00;
    DECLARE v_rate DECIMAL(5,4) DEFAULT 0.0620;
    DECLARE v_taxable DECIMAL(12,2);

    -- If already over the wage base, no more SS tax
    IF p_ytd_gross >= v_wage_base THEN
        RETURN 0.00;
    END IF;

    -- If this paycheck would push over the wage base, only tax up to the limit
    IF (p_ytd_gross + p_gross_pay) > v_wage_base THEN
        SET v_taxable = v_wage_base - p_ytd_gross;
    ELSE
        SET v_taxable = p_gross_pay;
    END IF;

    RETURN ROUND(v_taxable * v_rate, 2);
END //

-- -----------------------------------------------------
-- Function: calculate_medicare
-- Calculates Medicare tax (1.45%, additional 0.9% over $200k)
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS calculate_medicare //
CREATE FUNCTION calculate_medicare(
    p_gross_pay DECIMAL(10,2),
    p_ytd_gross DECIMAL(12,2)
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_threshold DECIMAL(12,2) DEFAULT 200000.00;
    DECLARE v_base_rate DECIMAL(5,4) DEFAULT 0.0145;
    DECLARE v_additional_rate DECIMAL(5,4) DEFAULT 0.0090;
    DECLARE v_tax DECIMAL(10,2);
    DECLARE v_new_ytd DECIMAL(12,2);

    SET v_tax = ROUND(p_gross_pay * v_base_rate, 2);
    SET v_new_ytd = p_ytd_gross + p_gross_pay;

    -- Additional Medicare tax on earnings over $200k
    IF v_new_ytd > v_threshold THEN
        IF p_ytd_gross >= v_threshold THEN
            -- All of this check is over the threshold
            SET v_tax = v_tax + ROUND(p_gross_pay * v_additional_rate, 2);
        ELSE
            -- Only the portion over the threshold
            SET v_tax = v_tax + ROUND((v_new_ytd - v_threshold) * v_additional_rate, 2);
        END IF;
    END IF;

    RETURN v_tax;
END //

-- -----------------------------------------------------
-- Function: calculate_federal_tax
-- Simplified federal income tax using 2024 brackets
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS calculate_federal_tax //
CREATE FUNCTION calculate_federal_tax(
    p_gross_pay DECIMAL(10,2),
    p_pay_periods_per_year INT,
    p_filing_status ENUM('single','married','head_of_household'),
    p_allowances INT,
    p_additional_withholding DECIMAL(8,2),
    p_exempt TINYINT
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_annual_income DECIMAL(12,2);
    DECLARE v_allowance_amount DECIMAL(10,2) DEFAULT 4300.00;
    DECLARE v_taxable DECIMAL(12,2);
    DECLARE v_annual_tax DECIMAL(10,2) DEFAULT 0.00;

    IF p_exempt = 1 THEN
        RETURN 0.00;
    END IF;

    -- Annualize the gross pay
    SET v_annual_income = p_gross_pay * p_pay_periods_per_year;

    -- Subtract allowances
    SET v_taxable = v_annual_income - (p_allowances * v_allowance_amount);
    IF v_taxable <= 0 THEN
        RETURN ROUND(p_additional_withholding, 2);
    END IF;

    -- Simplified 2024 tax brackets (single)
    IF p_filing_status = 'single' OR p_filing_status = 'head_of_household' THEN
        IF v_taxable <= 11600 THEN
            SET v_annual_tax = v_taxable * 0.10;
        ELSEIF v_taxable <= 47150 THEN
            SET v_annual_tax = 1160 + (v_taxable - 11600) * 0.12;
        ELSEIF v_taxable <= 100525 THEN
            SET v_annual_tax = 5426 + (v_taxable - 47150) * 0.22;
        ELSEIF v_taxable <= 191950 THEN
            SET v_annual_tax = 17168.50 + (v_taxable - 100525) * 0.24;
        ELSEIF v_taxable <= 243725 THEN
            SET v_annual_tax = 39110.50 + (v_taxable - 191950) * 0.32;
        ELSEIF v_taxable <= 609350 THEN
            SET v_annual_tax = 55758.50 + (v_taxable - 243725) * 0.35;
        ELSE
            SET v_annual_tax = 183647.25 + (v_taxable - 609350) * 0.37;
        END IF;
    ELSEIF p_filing_status = 'married' THEN
        IF v_taxable <= 23200 THEN
            SET v_annual_tax = v_taxable * 0.10;
        ELSEIF v_taxable <= 94300 THEN
            SET v_annual_tax = 2320 + (v_taxable - 23200) * 0.12;
        ELSEIF v_taxable <= 201050 THEN
            SET v_annual_tax = 10852 + (v_taxable - 94300) * 0.22;
        ELSEIF v_taxable <= 383900 THEN
            SET v_annual_tax = 34337 + (v_taxable - 201050) * 0.24;
        ELSEIF v_taxable <= 487450 THEN
            SET v_annual_tax = 78221 + (v_taxable - 383900) * 0.32;
        ELSEIF v_taxable <= 731200 THEN
            SET v_annual_tax = 111357 + (v_taxable - 487450) * 0.35;
        ELSE
            SET v_annual_tax = 196669.50 + (v_taxable - 731200) * 0.37;
        END IF;
    END IF;

    -- Convert back to per-period amount and add additional withholding
    RETURN ROUND((v_annual_tax / p_pay_periods_per_year) + p_additional_withholding, 2);
END //

-- -----------------------------------------------------
-- Function: calculate_state_tax
-- Simplified state tax (flat rate by state)
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS calculate_state_tax //
CREATE FUNCTION calculate_state_tax(
    p_gross_pay DECIMAL(10,2),
    p_state VARCHAR(50),
    p_allowances INT,
    p_exempt TINYINT
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_rate DECIMAL(5,4) DEFAULT 0.0000;

    IF p_exempt = 1 THEN
        RETURN 0.00;
    END IF;

    -- Simplified flat state tax rates
    CASE p_state
        WHEN 'CA' THEN SET v_rate = 0.0725;
        WHEN 'NY' THEN SET v_rate = 0.0685;
        WHEN 'TX' THEN SET v_rate = 0.0000;  -- No state income tax
        WHEN 'FL' THEN SET v_rate = 0.0000;  -- No state income tax
        WHEN 'IL' THEN SET v_rate = 0.0495;
        WHEN 'AZ' THEN SET v_rate = 0.0250;
        WHEN 'WA' THEN SET v_rate = 0.0000;  -- No state income tax
        WHEN 'NV' THEN SET v_rate = 0.0000;  -- No state income tax
        WHEN 'PA' THEN SET v_rate = 0.0307;
        WHEN 'OH' THEN SET v_rate = 0.0400;
        ELSE SET v_rate = 0.0500;  -- Default rate for other states
    END CASE;

    -- Reduce slightly per allowance
    SET v_rate = GREATEST(v_rate - (p_allowances * 0.005), 0);

    RETURN ROUND(p_gross_pay * v_rate, 2);
END //

-- -----------------------------------------------------
-- Function: calculate_employee_gross_pay
-- Calculates gross pay for an employee in a given period
-- Uses salary or hourly rate from employee_positions
-- plus approved time entries for hourly workers
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS calculate_employee_gross_pay //
CREATE FUNCTION calculate_employee_gross_pay(
    p_employee_id INT,
    p_period_start DATE,
    p_period_end DATE
)
RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE v_salary DECIMAL(10,2);
    DECLARE v_hourly_rate DECIMAL(8,2);
    DECLARE v_pay_frequency ENUM('weekly','bi_weekly','semi_monthly','monthly');
    DECLARE v_regular_hours DECIMAL(10,2);
    DECLARE v_overtime_hours DECIMAL(10,2);
    DECLARE v_gross DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_overtime_rate DECIMAL(8,2);

    -- Get current position pay info
    SELECT current_salary, current_hourly_rate, pay_frequency
    INTO v_salary, v_hourly_rate, v_pay_frequency
    FROM employee_positions
    WHERE employee_id = p_employee_id AND is_current = 1
    LIMIT 1;

    IF v_salary IS NOT NULL AND v_salary > 0 THEN
        -- Salaried employee: divide annual salary by number of pay periods
        CASE v_pay_frequency
            WHEN 'weekly' THEN SET v_gross = v_salary / 52;
            WHEN 'bi_weekly' THEN SET v_gross = v_salary / 26;
            WHEN 'semi_monthly' THEN SET v_gross = v_salary / 24;
            WHEN 'monthly' THEN SET v_gross = v_salary / 12;
        END CASE;
    ELSEIF v_hourly_rate IS NOT NULL AND v_hourly_rate > 0 THEN
        -- Hourly employee: calculate from approved time entries
        SELECT COALESCE(SUM(regular_hours), 0),
               COALESCE(SUM(overtime_hours), 0)
        INTO v_regular_hours, v_overtime_hours
        FROM time_entries
        WHERE employee_id = p_employee_id
          AND entry_date BETWEEN p_period_start AND p_period_end
          AND approved = 1;

        SET v_overtime_rate = v_hourly_rate * 1.5;
        SET v_gross = (v_regular_hours * v_hourly_rate) + (v_overtime_hours * v_overtime_rate);
    END IF;

    RETURN ROUND(v_gross, 2);
END //

-- -----------------------------------------------------
-- Function: get_pay_periods_per_year
-- Returns the number of pay periods per year for a frequency
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS get_pay_periods_per_year //
CREATE FUNCTION get_pay_periods_per_year(
    p_frequency ENUM('weekly','bi_weekly','semi_monthly','monthly')
)
RETURNS INT
DETERMINISTIC
BEGIN
    CASE p_frequency
        WHEN 'weekly' THEN RETURN 52;
        WHEN 'bi_weekly' THEN RETURN 26;
        WHEN 'semi_monthly' THEN RETURN 24;
        WHEN 'monthly' THEN RETURN 12;
    END CASE;
    RETURN 26; -- default
END //

-- -----------------------------------------------------
-- Function: get_ytd_gross
-- Returns the year-to-date gross pay for an employee
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS get_ytd_gross //
CREATE FUNCTION get_ytd_gross(
    p_employee_id INT,
    p_year INT
)
RETURNS DECIMAL(12,2)
READS SQL DATA
BEGIN
    DECLARE v_ytd DECIMAL(12,2);

    SELECT COALESCE(SUM(pc.gross_pay), 0)
    INTO v_ytd
    FROM paychecks pc
    JOIN pay_periods pp ON pc.pay_period_id = pp.pay_period_id
    WHERE pc.employee_id = p_employee_id
      AND YEAR(pp.period_start_date) = p_year
      AND pc.payment_status != 'void';

    RETURN v_ytd;
END //

DELIMITER ;
