"""
Database Setup Script
Creates all tables, indexes, and triggers for the payroll system.
Run this once to initialize a fresh database.
"""

from db_connection import get_connection


TABLES = {
    "employees": """
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INT NOT NULL AUTO_INCREMENT,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) DEFAULT NULL,
            address VARCHAR(255) DEFAULT NULL,
            city VARCHAR(50) DEFAULT NULL,
            state VARCHAR(50) DEFAULT NULL,
            zip_code VARCHAR(10) DEFAULT NULL,
            date_of_birth DATE DEFAULT NULL,
            hire_date DATE NOT NULL,
            termination_date DATE DEFAULT NULL,
            ssn VARCHAR(11) DEFAULT NULL,
            employment_status ENUM('active','terminated','on_leave') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (employee_id),
            UNIQUE KEY (email),
            UNIQUE KEY (ssn)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """,

    "departments": """
        CREATE TABLE IF NOT EXISTS departments (
            department_id INT NOT NULL AUTO_INCREMENT,
            department_name VARCHAR(100) NOT NULL,
            manager_id INT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (department_id),
            FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """,

    "positions": """
        CREATE TABLE IF NOT EXISTS positions (
            position_id INT NOT NULL AUTO_INCREMENT,
            position_title VARCHAR(100) NOT NULL,
            department_id INT DEFAULT NULL,
            base_salary DECIMAL(10,2) DEFAULT NULL,
            hourly_rate DECIMAL(8,2) DEFAULT NULL,
            employment_type ENUM('full_time','part_time','contract') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (position_id),
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """,

    "employee_positions": """
        CREATE TABLE IF NOT EXISTS employee_positions (
            emp_position_id INT NOT NULL AUTO_INCREMENT,
            employee_id INT NOT NULL,
            position_id INT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE DEFAULT NULL,
            current_salary DECIMAL(10,2) DEFAULT NULL,
            current_hourly_rate DECIMAL(8,2) DEFAULT NULL,
            pay_frequency ENUM('weekly','bi_weekly','semi_monthly','monthly') NOT NULL,
            is_current TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (emp_position_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (position_id) REFERENCES positions(position_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """,

    "pay_periods": """
        CREATE TABLE IF NOT EXISTS pay_periods (
            pay_period_id INT NOT NULL AUTO_INCREMENT,
            period_start_date DATE NOT NULL,
            period_end_date DATE NOT NULL,
            pay_date DATE NOT NULL,
            period_type ENUM('weekly','bi_weekly','semi_monthly','monthly') NOT NULL,
            status ENUM('open','processing','paid','closed') DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (pay_period_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """,

    "paychecks": """
        CREATE TABLE IF NOT EXISTS paychecks (
            paycheck_id INT NOT NULL AUTO_INCREMENT,
            employee_id INT NOT NULL,
            pay_period_id INT NOT NULL,
            check_number VARCHAR(50) DEFAULT NULL,
            gross_pay DECIMAL(10,2) NOT NULL,
            net_pay DECIMAL(10,2) NOT NULL,
            federal_tax DECIMAL(10,2) DEFAULT 0.00,
            state_tax DECIMAL(10,2) DEFAULT 0.00,
            social_security DECIMAL(10,2) DEFAULT 0.00,
            medicare DECIMAL(10,2) DEFAULT 0.00,
            health_insurance DECIMAL(10,2) DEFAULT 0.00,
            retirement_401k DECIMAL(10,2) DEFAULT 0.00,
            other_deductions DECIMAL(10,2) DEFAULT 0.00,
            payment_method ENUM('direct_deposit','check','cash') DEFAULT 'direct_deposit',
            payment_status ENUM('pending','processed','paid','void') DEFAULT 'pending',
            payment_date DATE DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (paycheck_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (pay_period_id) REFERENCES pay_periods(pay_period_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """,

    "tax_information": """
        CREATE TABLE IF NOT EXISTS tax_information (
            tax_id INT NOT NULL AUTO_INCREMENT,
            employee_id INT NOT NULL,
            filing_status ENUM('single','married','head_of_household') NOT NULL,
            federal_allowances INT DEFAULT 0,
            state_allowances INT DEFAULT 0,
            additional_withholding DECIMAL(8,2) DEFAULT 0.00,
            exempt_federal TINYINT(1) DEFAULT 0,
            exempt_state TINYINT(1) DEFAULT 0,
            effective_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (tax_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """,

    "time_entries": """
        CREATE TABLE IF NOT EXISTS time_entries (
            entry_id INT NOT NULL AUTO_INCREMENT,
            employee_id INT NOT NULL,
            entry_date DATE NOT NULL,
            clock_in TIME DEFAULT NULL,
            clock_out TIME DEFAULT NULL,
            regular_hours DECIMAL(5,2) DEFAULT 0.00,
            overtime_hours DECIMAL(5,2) DEFAULT 0.00,
            entry_type ENUM('work','sick','vacation','holiday','unpaid') DEFAULT 'work',
            notes TEXT,
            approved TINYINT(1) DEFAULT 0,
            approved_by INT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (entry_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (approved_by) REFERENCES employees(employee_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """,
}

INDEXES = [
    "CREATE INDEX idx_employees_status ON employees (employment_status)",
    "CREATE INDEX idx_employees_name ON employees (last_name, first_name)",
    "CREATE INDEX idx_employees_hire_date ON employees (hire_date)",
    "CREATE INDEX idx_time_entries_emp_date ON time_entries (employee_id, entry_date)",
    "CREATE INDEX idx_time_entries_approved ON time_entries (approved)",
    "CREATE INDEX idx_time_entries_type ON time_entries (entry_type)",
    "CREATE INDEX idx_paychecks_status ON paychecks (payment_status)",
    "CREATE INDEX idx_paychecks_payment_date ON paychecks (payment_date)",
    "CREATE INDEX idx_paychecks_emp_status ON paychecks (employee_id, payment_status)",
    "CREATE INDEX idx_pay_periods_status ON pay_periods (status)",
    "CREATE INDEX idx_pay_periods_dates ON pay_periods (period_start_date, period_end_date)",
    "CREATE INDEX idx_emp_positions_current ON employee_positions (employee_id, is_current)",
    "CREATE INDEX idx_tax_info_emp_date ON tax_information (employee_id, effective_date)",
]


def create_tables():
    """Creates all tables in the correct order."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table creation order matters due to foreign keys
    table_order = [
        "employees", "departments", "positions", "employee_positions",
        "pay_periods", "paychecks", "tax_information", "time_entries",
    ]

    for table_name in table_order:
        print(f"Creating table: {table_name}...")
        cursor.execute(TABLES[table_name])

    conn.commit()
    cursor.close()
    conn.close()
    print("All tables created successfully.")


def create_indexes():
    """Creates performance indexes. Skips any that already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    for index_sql in INDEXES:
        try:
            cursor.execute(index_sql)
            index_name = index_sql.split("INDEX ")[1].split(" ON")[0]
            print(f"Created index: {index_name}")
        except Exception as e:
            if "Duplicate key name" in str(e):
                pass  # Index already exists
            else:
                print(f"Warning: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("All indexes created successfully.")


def setup_database():
    """Full database setup: tables + indexes."""
    print("=== Payroll System Database Setup ===\n")
    create_tables()
    print()
    create_indexes()
    print("\nDatabase setup complete.")


if __name__ == "__main__":
    setup_database()
