"""
Tests for Backend/Services/paycheck_service.py

Covers: federal tax calculation, check number generation, paycheck CRUD,
duplicate prevention, status updates, and payroll run.
"""
import pytest
from datetime import date, timedelta
from fastapi import HTTPException

from Backend.Services.paycheck_service import (
    _calc_federal_tax,
    _generate_check_number,
    calculate_paycheck,
    create_paycheck,
    get_all_paychecks,
    get_paychecks_by_employee,
    get_paychecks_by_period,
    update_paycheck_status,
    run_payroll,
)
from Backend.Schemas.Paycheck import PaycheckCreate, PaycheckStatusUpdate
from Backend.Models.Paychecks import Paychecks
from Backend.Models.pay_periods import PayPeriods


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_period(db, start: date, weeks: int = 2, ptype: str = "bi_weekly",
                 status: str = "open") -> PayPeriods:
    end = start + timedelta(days=weeks * 7 - 1)
    pay = end + timedelta(days=6)
    p = PayPeriods(
        period_start_date=start,
        period_end_date=end,
        pay_date=pay,
        period_type=ptype,
        status=status,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _make_paycheck_data(employee_id: int, pay_period_id: int) -> PaycheckCreate:
    return PaycheckCreate(
        employee_id=employee_id,
        pay_period_id=pay_period_id,
        gross_pay=2000.0,
        net_pay=1560.0,
        federal_tax=200.0,
        state_tax=100.0,
        social_security=124.0,
        medicare=29.0,
        payment_method="direct deposit",
        payment_status="pending",
    )


# ── Federal tax calculation ────────────────────────────────────────────────────

class TestCalcFederalTax:
    def test_zero_income_returns_zero(self):
        assert _calc_federal_tax(0.0, 0) == 0.0

    def test_low_income_uses_10_percent_bracket(self):
        # $400 gross, 0 allowances → all in 10% bracket → $40.00
        tax = _calc_federal_tax(400.0, 0)
        assert tax == pytest.approx(40.0, abs=0.01)

    def test_allowances_reduce_taxable_income(self):
        # Each allowance = $175 reduction
        tax_none = _calc_federal_tax(1000.0, 0)
        tax_two = _calc_federal_tax(1000.0, 2)   # $350 reduction
        assert tax_two < tax_none

    def test_high_income_crosses_multiple_brackets(self):
        # $10 000 should span several brackets
        tax = _calc_federal_tax(10000.0, 0)
        assert tax > 0
        assert tax < 10000.0

    def test_allowances_exceeding_income_results_in_zero_tax(self):
        # 100 allowances × $175 = $17 500 > $500 gross → taxable = 0
        tax = _calc_federal_tax(500.0, 100)
        assert tax == 0.0

    def test_result_is_rounded_to_two_decimals(self):
        tax = _calc_federal_tax(750.0, 0)
        assert tax == round(tax, 2)


# ── Check number generator ─────────────────────────────────────────────────────

class TestGenerateCheckNumber:
    def test_starts_with_CHK_prefix(self):
        assert _generate_check_number().startswith("CHK-")

    def test_has_correct_length(self):
        # "CHK-" (4) + 8 digits = 12 characters
        assert len(_generate_check_number()) == 12

    def test_digits_only_after_prefix(self):
        num = _generate_check_number()[4:]
        assert num.isdigit()

    def test_generates_unique_values(self):
        generated = {_generate_check_number() for _ in range(200)}
        # With 10^8 possible values, 200 draws should all be unique
        assert len(generated) > 190


# ── Calculate paycheck ─────────────────────────────────────────────────────────

class TestCalculatePaycheck:
    def test_employee_not_found_raises_404(self, db):
        period = _make_period(db, date(2025, 1, 1))
        with pytest.raises(HTTPException) as exc:
            calculate_paycheck(99999, period.pay_period_id, db)
        assert exc.value.status_code == 404

    def test_pay_period_not_found_raises_404(self, db, sample_employee):
        with pytest.raises(HTTPException) as exc:
            calculate_paycheck(sample_employee.employee_id, 99999, db)
        assert exc.value.status_code == 404

    def test_no_position_gives_zero_gross(self, db, sample_employee):
        period = _make_period(db, date(2025, 2, 1))
        result = calculate_paycheck(sample_employee.employee_id, period.pay_period_id, db)
        assert result["gross_pay"] == 0.0
        assert result["net_pay"] == 0.0

    def test_result_contains_required_keys(self, db, sample_employee):
        period = _make_period(db, date(2025, 3, 1))
        result = calculate_paycheck(sample_employee.employee_id, period.pay_period_id, db)
        for key in ("gross_pay", "net_pay", "federal_tax", "state_tax",
                    "social_security", "medicare"):
            assert key in result


# ── Create paycheck ────────────────────────────────────────────────────────────

class TestCreatePaycheck:
    def test_create_success(self, db, sample_employee):
        period = _make_period(db, date(2025, 4, 1))
        data = _make_paycheck_data(sample_employee.employee_id, period.pay_period_id)
        paycheck = create_paycheck(data, db)
        assert paycheck.paycheck_id is not None
        assert paycheck.gross_pay == 2000.0

    def test_check_number_auto_generated_if_not_provided(self, db, sample_employee):
        period = _make_period(db, date(2025, 5, 1))
        data = _make_paycheck_data(sample_employee.employee_id, period.pay_period_id)
        paycheck = create_paycheck(data, db)
        assert paycheck.check_number is not None
        assert paycheck.check_number.startswith("CHK-")

    def test_custom_check_number_stored(self, db, sample_employee):
        period = _make_period(db, date(2025, 6, 1))
        data = _make_paycheck_data(sample_employee.employee_id, period.pay_period_id)
        data.check_number = "CHK-CUSTOM01"
        paycheck = create_paycheck(data, db)
        assert paycheck.check_number == "CHK-CUSTOM01"

    def test_duplicate_raises_409(self, db, sample_employee):
        period = _make_period(db, date(2025, 7, 1))
        data = _make_paycheck_data(sample_employee.employee_id, period.pay_period_id)
        create_paycheck(data, db)
        with pytest.raises(HTTPException) as exc:
            create_paycheck(data, db)
        assert exc.value.status_code == 409


# ── Get paychecks ──────────────────────────────────────────────────────────────

class TestGetAllPaychecks:
    def test_empty_returns_list(self, db):
        assert get_all_paychecks(db) == []

    def test_returns_created_paychecks(self, db, sample_employee):
        period = _make_period(db, date(2025, 8, 1))
        create_paycheck(_make_paycheck_data(sample_employee.employee_id, period.pay_period_id), db)
        assert len(get_all_paychecks(db)) == 1


class TestGetPaychecksByEmployee:
    def test_returns_paychecks_for_employee(self, db, sample_employee):
        period = _make_period(db, date(2025, 9, 1))
        create_paycheck(_make_paycheck_data(sample_employee.employee_id, period.pay_period_id), db)
        result = get_paychecks_by_employee(sample_employee.employee_id, db)
        assert len(result) == 1

    def test_employee_not_found_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            get_paychecks_by_employee(99999, db)
        assert exc.value.status_code == 404


class TestGetPaychecksByPeriod:
    def test_returns_paychecks_for_period(self, db, sample_employee):
        period = _make_period(db, date(2025, 10, 1))
        create_paycheck(_make_paycheck_data(sample_employee.employee_id, period.pay_period_id), db)
        result = get_paychecks_by_period(period.pay_period_id, db)
        assert len(result) == 1

    def test_period_not_found_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            get_paychecks_by_period(99999, db)
        assert exc.value.status_code == 404


# ── Update paycheck status ─────────────────────────────────────────────────────

class TestUpdatePaycheckStatus:
    def _create_paycheck(self, db, employee_id, start: date) -> Paychecks:
        period = _make_period(db, start)
        data = _make_paycheck_data(employee_id, period.pay_period_id)
        return create_paycheck(data, db)

    def test_update_to_paid(self, db, sample_employee):
        pc = self._create_paycheck(db, sample_employee.employee_id, date(2025, 11, 1))
        updated = update_paycheck_status(
            pc.paycheck_id,
            PaycheckStatusUpdate(payment_status="paid", payment_date=date(2025, 11, 20)),
            db,
        )
        assert updated.payment_status == "paid"
        assert updated.payment_date == date(2025, 11, 20)

    def test_update_to_void(self, db, sample_employee):
        pc = self._create_paycheck(db, sample_employee.employee_id, date(2025, 12, 1))
        updated = update_paycheck_status(
            pc.paycheck_id,
            PaycheckStatusUpdate(payment_status="void"),
            db,
        )
        assert updated.payment_status == "void"

    def test_not_found_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            update_paycheck_status(99999, PaycheckStatusUpdate(payment_status="paid"), db)
        assert exc.value.status_code == 404


# ── Run payroll ────────────────────────────────────────────────────────────────

class TestRunPayroll:
    def test_closed_period_raises_400(self, db):
        period = _make_period(db, date(2026, 1, 1), status="closed")
        with pytest.raises(HTTPException) as exc:
            run_payroll(period.pay_period_id, db)
        assert exc.value.status_code == 400

    def test_nonexistent_period_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            run_payroll(99999, db)
        assert exc.value.status_code == 404

    def test_run_with_no_active_employees_creates_zero_paychecks(self, db):
        period = _make_period(db, date(2026, 2, 1))
        result = run_payroll(period.pay_period_id, db)
        assert result["paychecks_created"] == 0
        assert result["pay_period_id"] == period.pay_period_id

    def test_period_status_set_to_processing_after_run(self, db):
        period = _make_period(db, date(2026, 3, 1))
        run_payroll(period.pay_period_id, db)
        db.refresh(period)
        assert period.status == "processing"
