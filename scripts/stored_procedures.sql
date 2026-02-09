-- =====================================================
-- Payroll System - Stored Procedures
-- Core business logic for payroll processing
-- =====================================================

USE payroll_system;

DELIMITER //

-- -----------------------------------------------------
-- Procedure: generate_paycheck
-- Creates a paycheck for a single employee in a pay period
-- Calculates gross pay, all taxes, and net pay
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS generate_paycheck //
CREATE PROCEDURE generate_paycheck(
    IN p_employee_id INT,
    IN p_pay_period_id INT,
    OUT p_paycheck_id INT
)
BEGIN
    DECLARE v_gross_pay DECIMAL(10,2);
    DECLARE v_federal_tax DECIMAL(10,2);
    DECLARE v_state_tax DECIMAL(10,2);
    DECLARE v_ss_tax DECIMAL(10,2);
    DECLARE v_medicare_tax DECIMAL(10,2);
    DECLARE v_health_ins DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_retirement DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_net_pay DECIMAL(10,2);
    DECLARE v_period_start DATE;
    DECLARE v_period_end DATE;
    DECLARE v_pay_date DATE;
    DECLARE v_emp_state VARCHAR(50);
    DECLARE v_filing_status ENUM('single','married','head_of_household');
    DECLARE v_fed_allowances INT;
    DECLARE v_state_allowances INT;
    DECLARE v_additional_withholding DECIMAL(8,2);
    DECLARE v_exempt_federal TINYINT;
    DECLARE v_exempt_state TINYINT;
    DECLARE v_pay_frequency ENUM('weekly','bi_weekly','semi_monthly','monthly');
    DECLARE v_periods_per_year INT;
    DECLARE v_ytd_gross DECIMAL(12,2);
    DECLARE v_check_number VARCHAR(50);
    DECLARE v_emp_status ENUM('active','terminated','on_leave');
    DECLARE v_payment_method ENUM('direct_deposit','check','cash') DEFAULT 'direct_deposit';

    -- Verify employee is active
    SELECT employment_status, state
    INTO v_emp_status, v_emp_state
    FROM employees
    WHERE employee_id = p_employee_id;

    IF v_emp_status != 'active' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot generate paycheck for non-active employee';
    END IF;

    -- Check for existing paycheck (prevent duplicates)
    IF EXISTS (
        SELECT 1 FROM paychecks
        WHERE employee_id = p_employee_id
          AND pay_period_id = p_pay_period_id
          AND payment_status != 'void'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Paycheck already exists for this employee and pay period';
    END IF;

    -- Get pay period dates
    SELECT period_start_date, period_end_date, pay_date
    INTO v_period_start, v_period_end, v_pay_date
    FROM pay_periods
    WHERE pay_period_id = p_pay_period_id;

    -- Get employee tax info
    SELECT filing_status, federal_allowances, state_allowances,
           additional_withholding, exempt_federal, exempt_state
    INTO v_filing_status, v_fed_allowances, v_state_allowances,
         v_additional_withholding, v_exempt_federal, v_exempt_state
    FROM tax_information
    WHERE employee_id = p_employee_id
    ORDER BY effective_date DESC
    LIMIT 1;

    -- Get pay frequency
    SELECT pay_frequency
    INTO v_pay_frequency
    FROM employee_positions
    WHERE employee_id = p_employee_id AND is_current = 1
    LIMIT 1;

    SET v_periods_per_year = get_pay_periods_per_year(v_pay_frequency);

    -- Calculate gross pay
    SET v_gross_pay = calculate_employee_gross_pay(p_employee_id, v_period_start, v_period_end);

    IF v_gross_pay <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Gross pay is zero. Check time entries or position assignment.';
    END IF;

    -- Get YTD gross for SS/Medicare calculations
    SET v_ytd_gross = get_ytd_gross(p_employee_id, YEAR(v_period_start));

    -- Calculate taxes
    SET v_federal_tax = calculate_federal_tax(
        v_gross_pay, v_periods_per_year, v_filing_status,
        v_fed_allowances, v_additional_withholding, v_exempt_federal
    );

    SET v_state_tax = calculate_state_tax(
        v_gross_pay, v_emp_state, v_state_allowances, v_exempt_state
    );

    SET v_ss_tax = calculate_social_security(v_gross_pay, v_ytd_gross);
    SET v_medicare_tax = calculate_medicare(v_gross_pay, v_ytd_gross);

    -- Calculate net pay
    SET v_net_pay = v_gross_pay - v_federal_tax - v_state_tax
                    - v_ss_tax - v_medicare_tax
                    - v_health_ins - v_retirement;

    -- Generate check number (format: YYYYMMDD-EMPID-PPID)
    SET v_check_number = CONCAT(
        DATE_FORMAT(v_pay_date, '%Y%m%d'), '-',
        LPAD(p_employee_id, 4, '0'), '-',
        LPAD(p_pay_period_id, 4, '0')
    );

    -- Insert the paycheck
    INSERT INTO paychecks (
        employee_id, pay_period_id, check_number,
        gross_pay, net_pay,
        federal_tax, state_tax, social_security, medicare,
        health_insurance, retirement_401k, other_deductions,
        payment_method, payment_status, payment_date
    ) VALUES (
        p_employee_id, p_pay_period_id, v_check_number,
        v_gross_pay, v_net_pay,
        v_federal_tax, v_state_tax, v_ss_tax, v_medicare_tax,
        v_health_ins, v_retirement, 0.00,
        v_payment_method, 'pending', v_pay_date
    );

    SET p_paycheck_id = LAST_INSERT_ID();
END //

-- -----------------------------------------------------
-- Procedure: process_pay_period
-- Generates paychecks for all active employees in a pay period
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS process_pay_period //
CREATE PROCEDURE process_pay_period(
    IN p_pay_period_id INT
)
BEGIN
    DECLARE v_emp_id INT;
    DECLARE v_paycheck_id INT;
    DECLARE v_period_status ENUM('open','processing','paid','closed');
    DECLARE v_success_count INT DEFAULT 0;
    DECLARE v_error_count INT DEFAULT 0;
    DECLARE v_done INT DEFAULT 0;

    DECLARE emp_cursor CURSOR FOR
        SELECT e.employee_id
        FROM employees e
        JOIN employee_positions ep ON e.employee_id = ep.employee_id
        WHERE e.employment_status = 'active'
          AND ep.is_current = 1;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_error_count = v_error_count + 1;

    -- Verify pay period status
    SELECT status INTO v_period_status
    FROM pay_periods
    WHERE pay_period_id = p_pay_period_id;

    IF v_period_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Pay period not found';
    END IF;

    IF v_period_status != 'open' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Pay period is not in open status';
    END IF;

    -- Set pay period to processing
    UPDATE pay_periods
    SET status = 'processing'
    WHERE pay_period_id = p_pay_period_id;

    -- Process each active employee
    OPEN emp_cursor;

    emp_loop: LOOP
        FETCH emp_cursor INTO v_emp_id;
        IF v_done THEN
            LEAVE emp_loop;
        END IF;

        CALL generate_paycheck(v_emp_id, p_pay_period_id, v_paycheck_id);

        IF v_paycheck_id IS NOT NULL THEN
            SET v_success_count = v_success_count + 1;
        END IF;
    END LOOP;

    CLOSE emp_cursor;

    -- Update pay period status based on results
    IF v_error_count = 0 AND v_success_count > 0 THEN
        UPDATE pay_periods
        SET status = 'paid'
        WHERE pay_period_id = p_pay_period_id;
    END IF;

    -- Return summary
    SELECT v_success_count AS paychecks_generated,
           v_error_count AS errors,
           v_period_status AS previous_status;
END //

-- -----------------------------------------------------
-- Procedure: terminate_employee
-- Handles employee termination: updates status,
-- closes current position, and prevents future time entries
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS terminate_employee //
CREATE PROCEDURE terminate_employee(
    IN p_employee_id INT,
    IN p_termination_date DATE
)
BEGIN
    DECLARE v_emp_status ENUM('active','terminated','on_leave');

    -- Verify employee exists and is not already terminated
    SELECT employment_status INTO v_emp_status
    FROM employees
    WHERE employee_id = p_employee_id;

    IF v_emp_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Employee not found';
    END IF;

    IF v_emp_status = 'terminated' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Employee is already terminated';
    END IF;

    -- Update employee record
    UPDATE employees
    SET employment_status = 'terminated',
        termination_date = p_termination_date
    WHERE employee_id = p_employee_id;

    -- Close all current positions
    UPDATE employee_positions
    SET is_current = 0,
        end_date = p_termination_date
    WHERE employee_id = p_employee_id
      AND is_current = 1;

    SELECT CONCAT('Employee ', p_employee_id, ' terminated as of ', p_termination_date) AS result;
END //

-- -----------------------------------------------------
-- Procedure: add_employee
-- Adds a new employee with position and tax information
-- in a single transaction
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS add_employee //
CREATE PROCEDURE add_employee(
    IN p_first_name VARCHAR(50),
    IN p_last_name VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_phone VARCHAR(20),
    IN p_address VARCHAR(255),
    IN p_city VARCHAR(50),
    IN p_state VARCHAR(50),
    IN p_zip_code VARCHAR(10),
    IN p_date_of_birth DATE,
    IN p_hire_date DATE,
    IN p_ssn VARCHAR(11),
    IN p_position_id INT,
    IN p_salary DECIMAL(10,2),
    IN p_hourly_rate DECIMAL(8,2),
    IN p_pay_frequency ENUM('weekly','bi_weekly','semi_monthly','monthly'),
    IN p_filing_status ENUM('single','married','head_of_household'),
    IN p_federal_allowances INT,
    IN p_state_allowances INT,
    OUT p_new_employee_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Insert employee
    INSERT INTO employees (
        first_name, last_name, email, phone,
        address, city, state, zip_code,
        date_of_birth, hire_date, ssn, employment_status
    ) VALUES (
        p_first_name, p_last_name, p_email, p_phone,
        p_address, p_city, p_state, p_zip_code,
        p_date_of_birth, p_hire_date, p_ssn, 'active'
    );

    SET p_new_employee_id = LAST_INSERT_ID();

    -- Assign position
    INSERT INTO employee_positions (
        employee_id, position_id, start_date,
        current_salary, current_hourly_rate,
        pay_frequency, is_current
    ) VALUES (
        p_new_employee_id, p_position_id, p_hire_date,
        p_salary, p_hourly_rate,
        p_pay_frequency, 1
    );

    -- Add tax information
    INSERT INTO tax_information (
        employee_id, filing_status,
        federal_allowances, state_allowances,
        effective_date
    ) VALUES (
        p_new_employee_id, p_filing_status,
        p_federal_allowances, p_state_allowances,
        p_hire_date
    );

    COMMIT;

    SELECT CONCAT('Employee ', p_first_name, ' ', p_last_name, ' added with ID ', p_new_employee_id) AS result;
END //

-- -----------------------------------------------------
-- Procedure: void_paycheck
-- Voids a paycheck and reverses the payment
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS void_paycheck //
CREATE PROCEDURE void_paycheck(
    IN p_paycheck_id INT,
    IN p_reason VARCHAR(255)
)
BEGIN
    DECLARE v_status ENUM('pending','processed','paid','void');

    SELECT payment_status INTO v_status
    FROM paychecks
    WHERE paycheck_id = p_paycheck_id;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Paycheck not found';
    END IF;

    IF v_status = 'void' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Paycheck is already voided';
    END IF;

    UPDATE paychecks
    SET payment_status = 'void'
    WHERE paycheck_id = p_paycheck_id;

    SELECT CONCAT('Paycheck ', p_paycheck_id, ' voided. Reason: ', p_reason) AS result;
END //

DELIMITER ;
