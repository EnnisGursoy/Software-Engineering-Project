"""
Insert a demo Employee with NO linked User row, so the 'Generate Login'
button appears on their row in the admin Employees page. Useful for
demoing the legacy-employee provisioning flow without touching real data.

Usage
-----
    python -m scripts.seed_demo_unlinked_employee
    python -m scripts.seed_demo_unlinked_employee --remove   # tear-down

Idempotent: re-running is a no-op if the demo row already exists.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from Backend.Database.connection import SessionLocal
from Backend.Models.Employee import Employee
from Backend.Models.User import User
from Backend.Utility.security import encrypt_ssn


DEMO_EMAIL = "demo.user@paycentral.test"
DEMO_SSN_PLAINTEXT = "234-56-7899"   # passes validate_ssn_format


def add_demo(db) -> str:
    existing = db.query(Employee).filter(Employee.email == DEMO_EMAIL).first()
    if existing:
        return f"Already exists (employee #{existing.employee_id}). Nothing to do."

    emp = Employee(
        first_name="Demo",
        last_name="User",
        email=DEMO_EMAIL,
        ssn=encrypt_ssn(DEMO_SSN_PLAINTEXT),
        hire_date=date(2024, 6, 1),
        employment_status="active",
        # user_id intentionally left NULL — this is the whole point
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return (
        f"Inserted demo employee #{emp.employee_id}: {emp.first_name} {emp.last_name} "
        f"<{emp.email}> with NO login attached.\n"
        "Refresh the Employees page in the browser — a blue 'Generate Login' button "
        "should now appear on the Demo User row."
    )


def remove_demo(db) -> str:
    emp = db.query(Employee).filter(Employee.email == DEMO_EMAIL).first()
    if not emp:
        return "No demo employee to remove."

    # If the demo row was given a login during the demo, also clean up that
    # User row so the email/username is freed for next time.
    if emp.user_id:
        user = db.query(User).filter(User.user_id == emp.user_id).first()
        if user:
            db.delete(user)

    db.delete(emp)
    db.commit()
    return f"Removed demo employee #{emp.employee_id} and any login it had."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Delete the demo employee (and any login it acquired) instead.",
    )
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        print(remove_demo(db) if args.remove else add_demo(db))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
