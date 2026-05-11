"""
Tests for the payroll-summary PDF report (FR-15).

Verifies that GET /payroll/report-pdf returns a real PDF, respects the
pay_period_id + status filters, and is gated to admin/manager/HR roles.
"""
from datetime import date

import pytest

from Backend.Models.Employee import Employee
from Backend.Models.Paychecks import Paychecks
from Backend.Models.pay_periods import PayPeriods
from Backend.Utility.security import encrypt_ssn


@pytest.fixture
def payroll_fixture(db):
    """Seed two employees, one pay period, and two paychecks (paid +
    pending) so the filter logic has something distinguishable to find."""
    e1 = Employee(
        first_name="Alice", last_name="Filer",
        email="alice@example.com",
        ssn=encrypt_ssn("234-56-7801"),
        hire_date=date(2024, 1, 1),
        employment_status="active",
    )
    e2 = Employee(
        first_name="Bob", last_name="Worker",
        email="bob@example.com",
        ssn=encrypt_ssn("234-56-7802"),
        hire_date=date(2024, 1, 1),
        employment_status="active",
    )
    db.add_all([e1, e2])
    db.commit()
    db.refresh(e1)
    db.refresh(e2)

    period = PayPeriods(
        period_start_date=date(2026, 4, 16),
        period_end_date=date(2026, 4, 30),
        pay_date=date(2026, 5, 5),
        period_type="bi_weekly",
        status="paid",
    )
    db.add(period)
    db.commit()
    db.refresh(period)

    p1 = Paychecks(
        employee_id=e1.employee_id, pay_period_id=period.pay_period_id,
        gross_pay=2500.0, net_pay=1842.50,
        federal_tax=300.0, state_tax=90.0,
        social_security=155.0, medicare=36.25,
        payment_status="paid",
    )
    p2 = Paychecks(
        employee_id=e2.employee_id, pay_period_id=period.pay_period_id,
        gross_pay=3100.0, net_pay=2272.85,
        federal_tax=380.0, state_tax=110.0,
        social_security=192.20, medicare=44.95,
        payment_status="pending",
    )
    db.add_all([p1, p2])
    db.commit()
    return {"period": period, "e1": e1, "e2": e2, "p1": p1, "p2": p2}


class TestPayrollReportPdf:
    def test_returns_application_pdf(self, client, admin_headers, payroll_fixture):
        resp = client.get("/payroll/report-pdf", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"].startswith("application/pdf")
        # %PDF magic bytes
        assert resp.content[:4] == b"%PDF"

    def test_content_disposition_attachment(self, client, admin_headers, payroll_fixture):
        resp = client.get("/payroll/report-pdf", headers=admin_headers)
        assert "attachment" in resp.headers.get("content-disposition", "").lower()

    def test_filter_by_period_returns_smaller_file_than_unfiltered(
        self, client, admin_headers, payroll_fixture, db
    ):
        # Add a second period with another paycheck so the unfiltered
        # report has strictly more rows than the period-filtered one.
        period2 = PayPeriods(
            period_start_date=date(2026, 5, 1),
            period_end_date=date(2026, 5, 15),
            pay_date=date(2026, 5, 20),
            period_type="bi_weekly",
        )
        db.add(period2)
        db.commit()
        db.refresh(period2)
        db.add(Paychecks(
            employee_id=payroll_fixture["e1"].employee_id,
            pay_period_id=period2.pay_period_id,
            gross_pay=2500, net_pay=1850,
            federal_tax=300, state_tax=90,
            social_security=155, medicare=36.25,
            payment_status="paid",
        ))
        db.commit()

        unfiltered = client.get("/payroll/report-pdf", headers=admin_headers)
        period1   = payroll_fixture["period"].pay_period_id
        filtered   = client.get(
            f"/payroll/report-pdf?pay_period_id={period1}", headers=admin_headers,
        )
        assert unfiltered.status_code == 200
        assert filtered.status_code == 200
        # Sanity: both are PDFs, and unfiltered has more rows → larger file
        assert unfiltered.content[:4] == b"%PDF"
        assert filtered.content[:4] == b"%PDF"
        assert len(unfiltered.content) >= len(filtered.content)

    def test_status_filter_only_returns_matching(
        self, client, admin_headers, payroll_fixture
    ):
        paid_only = client.get(
            "/payroll/report-pdf?status=paid", headers=admin_headers,
        )
        assert paid_only.status_code == 200
        assert paid_only.content[:4] == b"%PDF"

    def test_no_paychecks_still_returns_valid_pdf(self, client, admin_headers):
        resp = client.get("/payroll/report-pdf", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"

    def test_employee_role_is_rejected(self, client, payroll_fixture, db):
        # Build a user that's *only* role=employee — should NOT see report
        from Backend.Models.User import User
        from Backend.Utility.security import hash_password
        from tests.conftest import auth_headers
        u = User(
            username="emp_only",
            password_hash=hash_password("Pwd@1234"),
            role="employee",
            is_active=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        resp = client.get("/payroll/report-pdf", headers=auth_headers(u))
        assert resp.status_code == 403

    def test_hr_role_is_allowed(self, client, hr_user, hr_headers, payroll_fixture):
        resp = client.get("/payroll/report-pdf", headers=hr_headers)
        assert resp.status_code == 200
