"""
Migration script to add manager_user_id column to departments table
and backfill data for existing manager users.

Run with: python -m scripts.migrate_manager_user_id
"""
from Backend.Database.connection import SessionLocal, engine, Base
from Backend.Models.Department import Department
from Backend.Models.User import User
from Backend.Models.Employee import Employee
from sqlalchemy import text


def run_migration():
    db = SessionLocal()
    
    try:
        # Check if column exists
        result = db.execute(text("DESCRIBE departments"))
        columns = [row[0] for row in result]
        
        if 'manager_user_id' not in columns:
            print("Adding manager_user_id column to departments table...")
            db.execute(text("""
                ALTER TABLE departments 
                ADD COLUMN manager_user_id INT NULL
            """))
            db.commit()
            print("Column added successfully.")
        else:
            print("Column manager_user_id already exists.")
        
        # Check for existing FK constraint
        result = db.execute(text("SHOW CREATE TABLE departments"))
        create_stmt = result.fetchone()[1]
        
        if 'departments_ibfk_2' not in create_stmt:
            print("Adding foreign key constraint...")
            db.execute(text("""
                ALTER TABLE departments
                ADD CONSTRAINT departments_ibfk_2 
                FOREIGN KEY (manager_user_id) REFERENCES users(user_id)
            """))
            db.commit()
            print("Foreign key added successfully.")
        else:
            print("Foreign key already exists.")
        
        # Backfill manager_user_id for departments where manager has a user account
        print("\nBackfilling manager_user_id for existing departments...")
        
        # Get all departments with managers
        departments = db.query(Department).filter(Department.manager_id.isnot(None)).all()
        updated_count = 0
        
        for dept in departments:
            # Find the user linked to this manager's employee record
            employee = db.query(Employee).filter(
                Employee.employee_id == dept.manager_id,
                Employee.user_id.isnot(None)
            ).first()
            
            if employee and employee.user_id:
                dept.manager_user_id = employee.user_id
                updated_count += 1
        
        db.commit()
        print(f"Updated {updated_count} departments with manager_user_id.")
        
        # Summary
        print("\n--- Migration Summary ---")
        depts_with_manager_id = db.query(Department).filter(Department.manager_id.isnot(None)).count()
        depts_with_user_id = db.query(Department).filter(Department.manager_user_id.isnot(None)).count()
        print(f"Departments with manager_id: {depts_with_manager_id}")
        print(f"Departments with manager_user_id: {depts_with_user_id}")
        print("\nMigration complete!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
