"""
One-shot script: provision logins for existing Employees that don't have one.

Background
----------
Before the FR-2 fix, `/employee/sign_up` did NOT auto-create a User row, so
every employee added back then has `user_id IS NULL` and cannot sign in.
This script walks those rows, creates a User per employee with
`username = email` and a generated temp password, and prints a credentials
table the admin can hand out.

Usage
-----
    python -m scripts.backfill_employee_logins
    python -m scripts.backfill_employee_logins --dry-run    # report only
    python -m scripts.backfill_employee_logins --csv out.csv

Notes
-----
* Idempotent: re-running only touches employees still missing a login.
* If an Employee's email collides with an existing username, that row is
  skipped and reported in the "Skipped" section — fix manually.
* Department is inherited from the Employee row when present.
"""

from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterable

from Backend.Database.connection import SessionLocal
from Backend.Models.Employee import Employee
from Backend.Models.User import User
from Backend.Services.employee_service import _generate_temp_password
from Backend.Utility.security import hash_password


def find_unlinked_employees(db) -> list[Employee]:
    """Employees missing any User link — these are the ones that can't log in."""
    return (
        db.query(Employee)
        .filter(Employee.user_id.is_(None))
        .order_by(Employee.employee_id)
        .all()
    )


def provision_login_for(emp: Employee, db) -> tuple[str, str] | None:
    """Create a User for `emp`. Returns (username, temp_password) on success,
    or None if the username (= email) is already claimed."""
    if not emp.email:
        return None

    if db.query(User).filter(User.username == emp.email).first():
        return None  # collision — don't silently overwrite an existing account

    temp_pwd = _generate_temp_password()
    user = User(
        username=emp.email,
        password_hash=hash_password(temp_pwd),
        role="employee",
        first_name=emp.first_name,
        last_name=emp.last_name,
        department_id=emp.department_id,
        is_active=True,
    )
    db.add(user)
    db.flush()  # assign user_id without committing
    emp.user_id = user.user_id
    return emp.email, temp_pwd


def print_table(rows: Iterable[tuple[int, str, str, str, str]]) -> None:
    """Pretty ascii table — no third-party deps."""
    rows = list(rows)
    if not rows:
        print("  (none)")
        return
    headers = ("ID", "Name", "Email / Username", "Temp Password", "Status")
    widths = [
        max(len(str(r[i])) for r in [headers, *rows]) for i in range(len(headers))
    ]
    fmt = "  " + " | ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  " + "-+-".join("-" * w for w in widths))
    for r in rows:
        print(fmt.format(*r))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would happen without modifying the database.",
    )
    parser.add_argument(
        "--csv",
        metavar="PATH",
        help="Also write the credentials table to this CSV file.",
    )
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        targets = find_unlinked_employees(db)
        if not targets:
            print("All employees already have a login. Nothing to do.")
            return 0

        print(f"Found {len(targets)} employee(s) without a login.")
        if args.dry_run:
            print("(dry-run — no changes will be made)")

        provisioned: list[tuple[int, str, str, str, str]] = []
        skipped:     list[tuple[int, str, str, str, str]] = []

        for emp in targets:
            full_name = f"{emp.first_name} {emp.last_name}"
            if args.dry_run:
                provisioned.append(
                    (emp.employee_id, full_name, emp.email or "(no email)", "—", "WOULD CREATE")
                )
                continue

            result = provision_login_for(emp, db)
            if result is None:
                reason = "no email" if not emp.email else "username already exists"
                skipped.append(
                    (emp.employee_id, full_name, emp.email or "—", "—", f"SKIPPED ({reason})")
                )
            else:
                username, pwd = result
                provisioned.append(
                    (emp.employee_id, full_name, username, pwd, "CREATED")
                )

        if not args.dry_run:
            db.commit()

        print()
        print("Provisioned:")
        print_table(provisioned)
        if skipped:
            print()
            print("Skipped:")
            print_table(skipped)

        if args.csv and not args.dry_run:
            with open(args.csv, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["employee_id", "name", "username", "temp_password", "status"])
                w.writerows(provisioned + skipped)
            print()
            print(f"Wrote credentials to {args.csv}")

        print()
        print("Done. Share each temp password with the employee — they will be")
        print("prompted to change it on first sign-in.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
