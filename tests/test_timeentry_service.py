"""
Tests for Backend/Services/timeentry_service.py

Covers: _calc_hours helper, create/read/update/approve/delete time entries.
"""
import pytest
from datetime import date, time
from fastapi import HTTPException

from Backend.Services.timeentry_service import (
    _calc_hours,
    create_time_entry,
    get_entries_by_employee,
    get_all_entries,
    get_pending_approvals,
    update_time_entry,
    approve_time_entry,
    delete_time_entry,
)
from Backend.Schemas.TimeEntry import TimeEntryCreate, TimeEntryUpdate


# ── _calc_hours ────────────────────────────────────────────────────────────────

class TestCalcHours:
    def test_exactly_8_hours_no_overtime(self):
        reg, ot = _calc_hours(time(9, 0), time(17, 0))
        assert reg == 8.0
        assert ot == 0.0

    def test_9_hours_has_1_hour_overtime(self):
        reg, ot = _calc_hours(time(8, 0), time(17, 0))
        assert reg == 8.0
        assert ot == 1.0

    def test_less_than_8_hours_no_overtime(self):
        reg, ot = _calc_hours(time(10, 0), time(14, 0))
        assert reg == 4.0
        assert ot == 0.0

    def test_midnight_crossover_counts_correctly(self):
        # 10 PM to 6 AM = 8 hours
        reg, ot = _calc_hours(time(22, 0), time(6, 0))
        assert reg == 8.0
        assert ot == 0.0

    def test_none_inputs_return_zeros(self):
        assert _calc_hours(None, None) == (0.0, 0.0)
        assert _calc_hours(None, time(17, 0)) == (0.0, 0.0)
        assert _calc_hours(time(9, 0), None) == (0.0, 0.0)

    def test_cap_regular_hours_at_8(self):
        # 12-hour shift: regular capped at 8, overtime = 4
        reg, ot = _calc_hours(time(6, 0), time(18, 0))
        assert reg == 8.0
        assert ot == 4.0


# ── Create time entry ──────────────────────────────────────────────────────────

class TestCreateTimeEntry:
    def test_with_explicit_hours(self, db, sample_employee):
        data = TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 1, 15),
            regular_hours=8.0,
            overtime_hours=0.0,
        )
        entry = create_time_entry(data, db)
        assert entry.entry_id is not None
        assert entry.regular_hours == 8.0
        assert entry.approved is False

    def test_auto_calc_from_clock_times(self, db, sample_employee):
        data = TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 1, 16),
            clock_in=time(9, 0),
            clock_out=time(18, 0),  # 9 hours → 8 regular + 1 overtime
        )
        entry = create_time_entry(data, db)
        assert entry.regular_hours == 8.0
        assert entry.overtime_hours == 1.0

    def test_new_entry_is_not_approved(self, db, sample_employee):
        data = TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 1, 17),
            regular_hours=7.0,
        )
        entry = create_time_entry(data, db)
        assert entry.approved is False

    def test_employee_not_found_raises_404(self, db):
        data = TimeEntryCreate(
            employee_id=99999,
            entry_date=date(2024, 1, 15),
            regular_hours=8.0,
        )
        with pytest.raises(HTTPException) as exc:
            create_time_entry(data, db)
        assert exc.value.status_code == 404

    def test_entry_type_defaults_to_work(self, db, sample_employee):
        data = TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 2, 1),
            regular_hours=8.0,
        )
        entry = create_time_entry(data, db)
        assert entry.entry_type == "work"


# ── Read ───────────────────────────────────────────────────────────────────────

class TestGetEntriesByEmployee:
    def test_returns_entries_for_employee(self, db, sample_employee):
        create_time_entry(TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 3, 1),
            regular_hours=8.0,
        ), db)
        result = get_entries_by_employee(sample_employee.employee_id, db)
        assert len(result) == 1

    def test_employee_not_found_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            get_entries_by_employee(99999, db)
        assert exc.value.status_code == 404


class TestGetAllEntries:
    def test_empty_returns_list(self, db):
        assert get_all_entries(db) == []

    def test_returns_all_entries(self, db, sample_employee):
        for d in [date(2024, 4, 1), date(2024, 4, 2)]:
            create_time_entry(TimeEntryCreate(
                employee_id=sample_employee.employee_id,
                entry_date=d,
                regular_hours=8.0,
            ), db)
        assert len(get_all_entries(db)) == 2


class TestGetPendingApprovals:
    def test_new_entries_are_pending(self, db, sample_employee):
        create_time_entry(TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 5, 1),
            regular_hours=6.0,
        ), db)
        pending = get_pending_approvals(db)
        assert len(pending) >= 1

    def test_approved_entry_not_in_pending(self, db, sample_employee):
        data = TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 5, 2),
            regular_hours=8.0,
        )
        entry = create_time_entry(data, db)
        entry.approved = True
        db.commit()
        pending = get_pending_approvals(db)
        assert not any(e.entry_id == entry.entry_id for e in pending)


# ── Update ─────────────────────────────────────────────────────────────────────

class TestUpdateTimeEntry:
    def _create_entry(self, db, employee_id, entry_date=date(2024, 6, 1)):
        data = TimeEntryCreate(
            employee_id=employee_id,
            entry_date=entry_date,
            regular_hours=6.0,
        )
        return create_time_entry(data, db)

    def test_update_notes(self, db, sample_employee):
        entry = self._create_entry(db, sample_employee.employee_id)
        updated = update_time_entry(entry.entry_id, TimeEntryUpdate(notes="Updated"), db)
        assert updated.notes == "Updated"

    def test_update_recalculates_hours_from_clock_times(self, db, sample_employee):
        entry = self._create_entry(db, sample_employee.employee_id, date(2024, 6, 2))
        updated = update_time_entry(
            entry.entry_id,
            TimeEntryUpdate(clock_in=time(8, 0), clock_out=time(18, 0)),
            db,
        )
        assert updated.regular_hours == 8.0
        assert updated.overtime_hours == 2.0

    def test_cannot_update_approved_entry(self, db, sample_employee):
        entry = self._create_entry(db, sample_employee.employee_id, date(2024, 6, 3))
        entry.approved = True
        db.commit()
        with pytest.raises(HTTPException) as exc:
            update_time_entry(entry.entry_id, TimeEntryUpdate(notes="nope"), db)
        assert exc.value.status_code == 400

    def test_not_found_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            update_time_entry(99999, TimeEntryUpdate(notes="x"), db)
        assert exc.value.status_code == 404


# ── Approve ────────────────────────────────────────────────────────────────────

class TestApproveTimeEntry:
    def test_approve_sets_approved_true(self, db, sample_employee):
        entry = create_time_entry(TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 7, 1),
            regular_hours=8.0,
        ), db)
        updated = approve_time_entry(entry.entry_id, sample_employee.employee_id, db)
        assert updated.approved is True
        assert updated.approved_by == sample_employee.employee_id

    def test_approve_nonexistent_entry_raises_404(self, db, sample_employee):
        with pytest.raises(HTTPException) as exc:
            approve_time_entry(99999, sample_employee.employee_id, db)
        assert exc.value.status_code == 404

    def test_approve_with_nonexistent_approver_raises_404(self, db, sample_employee):
        entry = create_time_entry(TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 7, 2),
            regular_hours=8.0,
        ), db)
        with pytest.raises(HTTPException) as exc:
            approve_time_entry(entry.entry_id, 99999, db)
        assert exc.value.status_code == 404

    def test_approve_with_none_approver_succeeds(self, db, sample_employee):
        # HR/admin users without a linked Employee can still approve;
        # approved_by is left NULL.
        entry = create_time_entry(TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 7, 3),
            regular_hours=8.0,
        ), db)
        updated = approve_time_entry(entry.entry_id, None, db)
        assert updated.approved is True
        assert updated.approved_by is None


# ── Delete ─────────────────────────────────────────────────────────────────────

class TestDeleteTimeEntry:
    def test_delete_pending_entry(self, db, sample_employee):
        entry = create_time_entry(TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 8, 1),
            regular_hours=4.0,
        ), db)
        result = delete_time_entry(entry.entry_id, db)
        assert "deleted" in result["message"].lower()

    def test_cannot_delete_approved_entry(self, db, sample_employee):
        entry = create_time_entry(TimeEntryCreate(
            employee_id=sample_employee.employee_id,
            entry_date=date(2024, 8, 2),
            regular_hours=4.0,
        ), db)
        entry.approved = True
        db.commit()
        with pytest.raises(HTTPException) as exc:
            delete_time_entry(entry.entry_id, db)
        assert exc.value.status_code == 400

    def test_delete_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            delete_time_entry(99999, db)
        assert exc.value.status_code == 404
