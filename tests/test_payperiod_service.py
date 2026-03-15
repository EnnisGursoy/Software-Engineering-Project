"""
Tests for Backend/Services/PayPeriod_service.py

Covers: create (with overlap detection), get, update, and close pay periods.
"""
import pytest
from datetime import date, timedelta
from fastapi import HTTPException

from Backend.Services.PayPeriod_service import (
    get_all_pay_periods,
    get_pay_period,
    create_pay_period,
    update_pay_period,
    close_pay_period,
)
from Backend.Schemas.PayPeriods import PayPeriodCreate, PayPeriodUpdate


# ── Helpers ────────────────────────────────────────────────────────────────────

def _period(start: date, end: date, pay: date, ptype="bi_weekly", status="open"):
    return PayPeriodCreate(
        period_start_date=start,
        period_end_date=end,
        pay_date=pay,
        period_type=ptype,
        status=status,
    )


def _biweekly(offset_weeks: int = 0):
    """Helper that creates a non-overlapping bi_weekly period."""
    start = date(2025, 1, 1) + timedelta(weeks=offset_weeks * 2)
    end = start + timedelta(days=13)
    pay = end + timedelta(days=6)
    return _period(start, end, pay)


# ── Create ─────────────────────────────────────────────────────────────────────

class TestCreatePayPeriod:
    def test_create_success(self, db):
        p = create_pay_period(_biweekly(0), db)
        assert p.pay_period_id is not None
        assert p.status == "open"
        assert p.period_type == "bi_weekly"

    def test_default_status_is_open(self, db):
        data = _period(date(2025, 3, 1), date(2025, 3, 14), date(2025, 3, 20))
        p = create_pay_period(data, db)
        assert p.status == "open"

    def test_overlapping_period_same_type_raises_409(self, db):
        create_pay_period(_biweekly(0), db)
        # Shift start by only 1 week — fully inside the previous period
        start = date(2025, 1, 7)
        end = date(2025, 1, 20)
        pay = date(2025, 1, 26)
        with pytest.raises(HTTPException) as exc:
            create_pay_period(_period(start, end, pay), db)
        assert exc.value.status_code == 409

    def test_non_overlapping_same_type_succeeds(self, db):
        create_pay_period(_biweekly(0), db)  # Jan 1-14
        p2 = create_pay_period(_biweekly(1), db)  # Jan 15-28
        assert p2.pay_period_id is not None

    def test_overlapping_dates_different_type_allowed(self, db):
        # bi_weekly period exists; monthly period with same dates should be OK
        create_pay_period(_biweekly(0), db)
        monthly = _period(date(2025, 1, 1), date(2025, 1, 31), date(2025, 2, 5), ptype="monthly")
        p = create_pay_period(monthly, db)
        assert p is not None

    def test_closed_period_does_not_block_new_one(self, db):
        p = create_pay_period(_biweekly(0), db)
        close_pay_period(p.pay_period_id, db)
        # Same dates, same type — but previous is closed → should not overlap
        p2 = create_pay_period(_biweekly(0), db)
        assert p2.pay_period_id is not None


# ── Get ────────────────────────────────────────────────────────────────────────

class TestGetPayPeriod:
    def test_get_existing(self, db):
        created = create_pay_period(_biweekly(2), db)
        found = get_pay_period(created.pay_period_id, db)
        assert found.pay_period_id == created.pay_period_id

    def test_get_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            get_pay_period(99999, db)
        assert exc.value.status_code == 404


class TestGetAllPayPeriods:
    def test_empty_returns_list(self, db):
        assert get_all_pay_periods(db) == []

    def test_returns_all_periods(self, db):
        create_pay_period(_biweekly(3), db)
        create_pay_period(_biweekly(4), db)
        assert len(get_all_pay_periods(db)) == 2


# ── Update ─────────────────────────────────────────────────────────────────────

class TestUpdatePayPeriod:
    def test_update_pay_date(self, db):
        p = create_pay_period(_biweekly(5), db)
        new_pay_date = date(2026, 1, 1)
        updated = update_pay_period(p.pay_period_id, PayPeriodUpdate(pay_date=new_pay_date), db)
        assert updated.pay_date == new_pay_date

    def test_update_status(self, db):
        p = create_pay_period(_biweekly(6), db)
        updated = update_pay_period(p.pay_period_id, PayPeriodUpdate(status="processing"), db)
        assert updated.status == "processing"

    def test_cannot_update_closed_period(self, db):
        p = create_pay_period(_biweekly(7), db)
        close_pay_period(p.pay_period_id, db)
        with pytest.raises(HTTPException) as exc:
            update_pay_period(p.pay_period_id, PayPeriodUpdate(status="open"), db)
        assert exc.value.status_code == 400

    def test_update_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            update_pay_period(99999, PayPeriodUpdate(status="processing"), db)
        assert exc.value.status_code == 404


# ── Close ──────────────────────────────────────────────────────────────────────

class TestClosePayPeriod:
    def test_close_open_period(self, db):
        p = create_pay_period(_biweekly(8), db)
        result = close_pay_period(p.pay_period_id, db)
        assert "closed" in result["message"].lower()
        db.refresh(p)
        assert p.status == "closed"

    def test_close_already_closed_returns_message(self, db):
        p = create_pay_period(_biweekly(9), db)
        close_pay_period(p.pay_period_id, db)
        result = close_pay_period(p.pay_period_id, db)
        assert "already closed" in result["message"].lower()

    def test_close_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            close_pay_period(99999, db)
        assert exc.value.status_code == 404
