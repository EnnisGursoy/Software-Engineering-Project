-- =====================================================
-- Payroll System - Triggers
-- Automatic enforcement of business rules
-- =====================================================

USE payroll_system;

DELIMITER //

-- -----------------------------------------------------
-- Trigger: trg_time_entry_calculate_hours
-- Auto-calculates regular and overtime hours from
-- clock_in and clock_out times on INSERT.
-- Anything over 8 hours in a day counts as overtime.
-- -----------------------------------------------------
DROP TRIGGER IF EXISTS trg_time_entry_calculate_hours //
CREATE TRIGGER trg_time_entry_calculate_hours
BEFORE INSERT ON time_entries
FOR EACH ROW
BEGIN
    DECLARE v_total_hours DECIMAL(5,2);

    IF NEW.clock_in IS NOT NULL AND NEW.clock_out IS NOT NULL THEN
        SET v_total_hours = ROUND(TIMESTAMPDIFF(MINUTE, NEW.clock_in, NEW.clock_out) / 60.0, 2);

        IF v_total_hours > 8.00 THEN
            SET NEW.regular_hours = 8.00;
            SET NEW.overtime_hours = v_total_hours - 8.00;
        ELSE
            SET NEW.regular_hours = v_total_hours;
            SET NEW.overtime_hours = 0.00;
        END IF;
    END IF;
END //

-- -----------------------------------------------------
-- Trigger: trg_time_entry_update_hours
-- Same as above but fires on UPDATE when clock times change
-- -----------------------------------------------------
DROP TRIGGER IF EXISTS trg_time_entry_update_hours //
CREATE TRIGGER trg_time_entry_update_hours
BEFORE UPDATE ON time_entries
FOR EACH ROW
BEGIN
    DECLARE v_total_hours DECIMAL(5,2);

    IF NEW.clock_in IS NOT NULL AND NEW.clock_out IS NOT NULL THEN
        IF NEW.clock_in != OLD.clock_in OR NEW.clock_out != OLD.clock_out THEN
            SET v_total_hours = ROUND(TIMESTAMPDIFF(MINUTE, NEW.clock_in, NEW.clock_out) / 60.0, 2);

            IF v_total_hours > 8.00 THEN
                SET NEW.regular_hours = 8.00;
                SET NEW.overtime_hours = v_total_hours - 8.00;
            ELSE
                SET NEW.regular_hours = v_total_hours;
                SET NEW.overtime_hours = 0.00;
            END IF;
        END IF;
    END IF;
END //

-- -----------------------------------------------------
-- Trigger: trg_prevent_terminated_time_entry
-- Prevents inserting time entries for terminated employees
-- -----------------------------------------------------
DROP TRIGGER IF EXISTS trg_prevent_terminated_time_entry //
CREATE TRIGGER trg_prevent_terminated_time_entry
BEFORE INSERT ON time_entries
FOR EACH ROW
BEGIN
    DECLARE v_status ENUM('active','terminated','on_leave');

    SELECT employment_status INTO v_status
    FROM employees
    WHERE employee_id = NEW.employee_id;

    IF v_status = 'terminated' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot add time entries for a terminated employee';
    END IF;
END //

-- -----------------------------------------------------
-- Trigger: trg_employee_termination_cleanup
-- When an employee is terminated, automatically close
-- their current position assignments
-- -----------------------------------------------------
DROP TRIGGER IF EXISTS trg_employee_termination_cleanup //
CREATE TRIGGER trg_employee_termination_cleanup
AFTER UPDATE ON employees
FOR EACH ROW
BEGIN
    IF OLD.employment_status != 'terminated' AND NEW.employment_status = 'terminated' THEN
        UPDATE employee_positions
        SET is_current = 0,
            end_date = COALESCE(NEW.termination_date, CURDATE())
        WHERE employee_id = NEW.employee_id
          AND is_current = 1;
    END IF;
END //

-- -----------------------------------------------------
-- Trigger: trg_prevent_duplicate_active_position
-- Ensures an employee can only have one current position
-- at a time
-- -----------------------------------------------------
DROP TRIGGER IF EXISTS trg_prevent_duplicate_active_position //
CREATE TRIGGER trg_prevent_duplicate_active_position
BEFORE INSERT ON employee_positions
FOR EACH ROW
BEGIN
    DECLARE v_active_count INT;

    IF NEW.is_current = 1 THEN
        SELECT COUNT(*) INTO v_active_count
        FROM employee_positions
        WHERE employee_id = NEW.employee_id
          AND is_current = 1;

        IF v_active_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Employee already has an active position. Close the current one first.';
        END IF;
    END IF;
END //

-- -----------------------------------------------------
-- Trigger: trg_paycheck_status_date
-- Automatically sets payment_date when paycheck status
-- changes to 'paid'
-- -----------------------------------------------------
DROP TRIGGER IF EXISTS trg_paycheck_status_date //
CREATE TRIGGER trg_paycheck_status_date
BEFORE UPDATE ON paychecks
FOR EACH ROW
BEGIN
    IF OLD.payment_status != 'paid' AND NEW.payment_status = 'paid' THEN
        IF NEW.payment_date IS NULL THEN
            SET NEW.payment_date = CURDATE();
        END IF;
    END IF;
END //

DELIMITER ;
