"""
Tests for Backend/Services/Tax_service.py

Covers: create, read, update, delete, and list tax information records.
"""
import pytest
from datetime import date
from fastapi import HTTPException

from Backend.Services.Tax_service import (
    create_tax,
    get_tax_by_employee,
    update_tax,
    delete_tax,
    list_all_tax,
)
from Backend.Schemas.Tax import TaxCreate, TaxUpdate


# ── Helpers ────────────────────────────────────────────────────────────────────

def _tax(employee_id: int, filing_status: str = "single") -> TaxCreate:
    return TaxCreate(
        employee_id=employee_id,
        filing_status=filing_status,
        federal_allowances=1,
        state_allowances=1,
        additional_withholding=0.0,
        exempt_state=False,
        exempt_federal=False,
        effective_date=date(2024, 1, 1),
    )


# ── Create ─────────────────────────────────────────────────────────────────────

class TestCreateTax:
    def test_create_success(self, db, sample_employee):
        tax = create_tax(_tax(sample_employee.employee_id), db)
        assert tax.tax_id is not None
        assert tax.employee_id == sample_employee.employee_id
        assert tax.filing_status == "single"

    def test_employee_not_found_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            create_tax(_tax(99999), db)
        assert exc.value.status_code == 404

    def test_stores_federal_allowances(self, db, sample_employee):
        data = _tax(sample_employee.employee_id)
        data.federal_allowances = 3
        tax = create_tax(data, db)
        assert tax.federal_allowances == 3

    def test_exempt_flags_stored_correctly(self, db, sample_employee):
        data = TaxCreate(
            employee_id=sample_employee.employee_id,
            filing_status="married",
            federal_allowances=2,
            state_allowances=2,
            exempt_federal=True,
            exempt_state=True,
            effective_date=date(2024, 6, 1),
        )
        tax = create_tax(data, db)
        assert tax.exempt_federal is True
        assert tax.exempt_state is True


# ── Read ───────────────────────────────────────────────────────────────────────

class TestGetTaxByEmployee:
    def test_returns_tax_for_existing_employee(self, db, sample_employee):
        create_tax(_tax(sample_employee.employee_id), db)
        tax = get_tax_by_employee(sample_employee.employee_id, db)
        assert tax.employee_id == sample_employee.employee_id

    def test_not_found_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            get_tax_by_employee(99999, db)
        assert exc.value.status_code == 404

    def test_returns_correct_record(self, db, sample_employee):
        create_tax(_tax(sample_employee.employee_id, filing_status="head_of_household"), db)
        tax = get_tax_by_employee(sample_employee.employee_id, db)
        assert tax.filing_status == "head_of_household"


# ── Update ─────────────────────────────────────────────────────────────────────

class TestUpdateTax:
    def test_update_filing_status(self, db, sample_employee):
        create_tax(_tax(sample_employee.employee_id), db)
        updated = update_tax(sample_employee.employee_id, TaxUpdate(filing_status="married"), db)
        assert updated.filing_status == "married"

    def test_update_federal_allowances(self, db, sample_employee):
        create_tax(_tax(sample_employee.employee_id), db)
        updated = update_tax(sample_employee.employee_id, TaxUpdate(federal_allowances=5), db)
        assert updated.federal_allowances == 5

    def test_update_exempt_flags(self, db, sample_employee):
        create_tax(_tax(sample_employee.employee_id), db)
        updated = update_tax(sample_employee.employee_id, TaxUpdate(exempt_federal=True), db)
        assert updated.exempt_federal is True

    def test_update_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            update_tax(99999, TaxUpdate(filing_status="single"), db)
        assert exc.value.status_code == 404


# ── Delete ─────────────────────────────────────────────────────────────────────

class TestDeleteTax:
    def test_delete_success(self, db, sample_employee):
        create_tax(_tax(sample_employee.employee_id), db)
        result = delete_tax(sample_employee.employee_id, db)
        assert "deleted" in result["message"].lower()

    def test_record_is_gone_after_delete(self, db, sample_employee):
        create_tax(_tax(sample_employee.employee_id), db)
        delete_tax(sample_employee.employee_id, db)
        with pytest.raises(HTTPException):
            get_tax_by_employee(sample_employee.employee_id, db)

    def test_delete_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            delete_tax(99999, db)
        assert exc.value.status_code == 404


# ── List all ───────────────────────────────────────────────────────────────────

class TestListAllTax:
    def test_empty_returns_empty_list(self, db):
        assert list_all_tax(db) == []

    def test_returns_all_records(self, db, sample_employee):
        create_tax(_tax(sample_employee.employee_id), db)
        result = list_all_tax(db)
        assert len(result) == 1

    def test_count_increases_with_more_employees(self, db, sample_employee):
        from Backend.Models.Employee import Employee
        from Backend.Utility.security import encrypt_ssn

        emp2 = Employee(
            first_name="Bob",
            last_name="Taxtest",
            email="bob.taxtest@example.com",
            hire_date=date(2023, 1, 1),
            ssn=encrypt_ssn("345-67-8901"),
            employment_status="active",
        )
        db.add(emp2)
        db.commit()
        db.refresh(emp2)

        create_tax(_tax(sample_employee.employee_id), db)
        create_tax(_tax(emp2.employee_id), db)
        assert len(list_all_tax(db)) == 2
