"""
Tests for Backend/Services/employee_service.py

Covers: SSN validation, duplicate checks, employee CRUD, soft/hard delete.
"""
import pytest
from datetime import date
from fastapi import HTTPException

from Backend.Services.employee_service import (
    validate_ssn_format,
    create_employee,
    show_employee,
    show_all_employees,
    update_employee,
    delete_employee,
    hard_delete_employee,
    get_employees_by_department,
)
from Backend.Schemas.Employee import EmployeeCreate, EmployeeUpdate
from Backend.Schemas.User import UserCreate
from Backend.Models.Employee import Employee
from Backend.Utility.security import encrypt_ssn


# ── SSN format validation ──────────────────────────────────────────────────────

class TestValidateSSNFormat:
    def test_valid_ssn_does_not_raise(self):
        validate_ssn_format("234-56-7890")  # must not raise

    def test_no_dashes_raises_403(self):
        with pytest.raises(HTTPException) as exc:
            validate_ssn_format("234567890")
        assert exc.value.status_code == 403

    def test_wrong_format_raises_403(self):
        with pytest.raises(HTTPException) as exc:
            validate_ssn_format("12-345-6789")
        assert exc.value.status_code == 403

    def test_ssn_starting_000_raises(self):
        with pytest.raises(HTTPException):
            validate_ssn_format("000-12-3456")

    def test_ssn_starting_666_raises(self):
        with pytest.raises(HTTPException):
            validate_ssn_format("666-12-3456")

    def test_ssn_starting_9xx_raises(self):
        with pytest.raises(HTTPException):
            validate_ssn_format("999-12-3456")

    def test_middle_group_00_raises(self):
        with pytest.raises(HTTPException):
            validate_ssn_format("234-00-3456")

    def test_last_group_0000_raises(self):
        with pytest.raises(HTTPException):
            validate_ssn_format("234-56-0000")


# ── Employee CRUD ──────────────────────────────────────────────────────────────

class TestCreateEmployee:
    def _make_data(self, last_name, ssn, email, dept_name=None):
        return EmployeeCreate(
            user=UserCreate(username=f"user_{last_name.lower()}", password="Pass@1234"),
            first_name="Test",
            last_name=last_name,
            email=email,
            hire_date=date(2023, 1, 1),
            ssn=ssn,
            department_name=dept_name,
        )

    def test_create_success_returns_employee(self, db):
        data = self._make_data("Creatable", "321-45-6789", "creatable@test.com")
        emp = create_employee(data, db)
        assert emp.employee_id is not None
        assert emp.first_name == "Test"
        assert emp.last_name == "Creatable"

    def test_ssn_is_stored_encrypted(self, db):
        data = self._make_data("Encrypted", "321-45-6780", "encrypted@test.com")
        emp = create_employee(data, db)
        # The stored SSN should not be the plaintext value
        assert emp.ssn != "321-45-6780"

    def test_invalid_ssn_raises_403(self, db):
        data = self._make_data("BadSSN", "000-00-0000", "badssn@test.com")
        with pytest.raises(HTTPException) as exc:
            create_employee(data, db)
        assert exc.value.status_code == 403

    def test_unknown_department_raises_404(self, db):
        data = self._make_data("NoDept", "432-56-7890", "nodept@test.com", dept_name="Ghost Dept")
        with pytest.raises(HTTPException) as exc:
            create_employee(data, db)
        assert exc.value.status_code == 404

    def test_known_department_assigns_department_id(self, db, sample_department):
        data = self._make_data("WithDept", "543-67-8901", "withdept@test.com",
                               dept_name="Engineering")
        emp = create_employee(data, db)
        assert emp.department_id == sample_department.department_id

    def test_default_employment_status_is_active(self, db):
        data = self._make_data("DefaultStatus", "654-78-9012", "defaultstatus@test.com")
        emp = create_employee(data, db)
        assert emp.employment_status == "active"


class TestShowEmployee:
    def test_found_returns_employee(self, db, sample_employee):
        result = show_employee(sample_employee.employee_id, db)
        assert result.employee_id == sample_employee.employee_id

    def test_not_found_raises_400(self, db):
        with pytest.raises(HTTPException) as exc:
            show_employee(99999, db)
        assert exc.value.status_code == 400


class TestShowAllEmployees:
    def test_empty_db_returns_empty_list(self, db):
        assert show_all_employees(db) == []

    def test_returns_all_created_employees(self, db, sample_employee):
        result = show_all_employees(db)
        assert any(e.employee_id == sample_employee.employee_id for e in result)


class TestUpdateEmployee:
    def test_update_email(self, db, sample_employee):
        data = EmployeeUpdate(email="updated@example.com")
        updated = update_employee(sample_employee.employee_id, data, db)
        assert updated.email == "updated@example.com"

    def test_update_city_and_state(self, db, sample_employee):
        data = EmployeeUpdate(city="Austin", state="TX")
        updated = update_employee(sample_employee.employee_id, data, db)
        assert updated.city == "Austin"
        assert updated.state == "TX"

    def test_update_nonexistent_raises_400(self, db):
        data = EmployeeUpdate(email="x@x.com")
        with pytest.raises(HTTPException) as exc:
            update_employee(99999, data, db)
        assert exc.value.status_code == 400


class TestDeleteEmployee:
    def test_soft_delete_sets_terminated(self, db, sample_employee):
        result = delete_employee(sample_employee.employee_id, db)
        db.refresh(sample_employee)
        assert sample_employee.employment_status == "terminated"
        assert "terminated" in result["message"].lower() or "already" in result["message"].lower()

    def test_soft_delete_on_already_terminated_returns_message(self, db, sample_employee):
        sample_employee.employment_status = "terminated"
        db.commit()
        result = delete_employee(sample_employee.employee_id, db)
        assert "already terminated" in result["message"]

    def test_soft_delete_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            delete_employee(99999, db)
        assert exc.value.status_code == 404


class TestHardDeleteEmployee:
    def test_hard_delete_removes_record(self, db, sample_employee):
        eid = sample_employee.employee_id
        result = hard_delete_employee(eid, db)
        assert db.query(Employee).filter(Employee.employee_id == eid).first() is None
        assert "deleted" in result["message"].lower()

    def test_hard_delete_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            hard_delete_employee(99999, db)
        assert exc.value.status_code == 404


class TestGetEmployeesByDepartment:
    def test_returns_employees_assigned_to_department(self, db, sample_employee, sample_department):
        sample_employee.department_id = sample_department.department_id
        db.commit()
        result = get_employees_by_department(sample_department.department_id, db)
        assert any(e.employee_id == sample_employee.employee_id for e in result)

    def test_returns_empty_for_department_with_no_employees(self, db, sample_department):
        result = get_employees_by_department(sample_department.department_id, db)
        assert result == []

    def test_does_not_return_employees_from_other_departments(self, db, sample_employee, sample_department):
        other_dept = __import__("Backend.Models.Department", fromlist=["Department"]).Department
        from Backend.Models.Department import Department
        other = Department(department_name="Finance", manager_id=None)
        db.add(other)
        db.commit()
        db.refresh(other)

        sample_employee.department_id = other.department_id
        db.commit()

        result = get_employees_by_department(sample_department.department_id, db)
        assert not any(e.employee_id == sample_employee.employee_id for e in result)
