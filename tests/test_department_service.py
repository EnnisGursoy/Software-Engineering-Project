"""
Tests for Backend/Services/Department_service.py

Covers: create, list, lookup by manager, delete, assign manager, get my dept.
"""
import pytest
from fastapi import HTTPException

from Backend.Services.Department_service import (
    create_department,
    show_department,
    get_department_by_manager_id,
    delete_department,
    assign_manager,
    get_my_department,
)
from Backend.Schemas.department import DepartmentCreate, DepartmentUpdate
from Backend.Models.Department import Department


# ── Helpers ────────────────────────────────────────────────────────────────────

def _dept(name: str, manager_id: int = 1) -> DepartmentCreate:
    # manager_id is required int in the schema; use 1 as a placeholder when
    # the actual employee doesn't matter (SQLite won't enforce the FK).
    return DepartmentCreate(department_name=name, manager_id=manager_id)


# ── Create ─────────────────────────────────────────────────────────────────────

class TestCreateDepartment:
    def test_create_returns_new_department(self, db):
        dept = create_department(_dept("Marketing"), db)
        assert dept.department_id is not None
        assert dept.department_name == "Marketing"

    def test_create_with_manager_id(self, db, sample_employee):
        dept = create_department(_dept("Sales", manager_id=sample_employee.employee_id), db)
        assert dept.manager_id == sample_employee.employee_id

    def test_duplicate_name_raises_400(self, db, sample_department):
        with pytest.raises(HTTPException) as exc:
            create_department(_dept("Engineering"), db)
        assert exc.value.status_code == 400

    def test_different_names_both_succeed(self, db):
        create_department(_dept("Alpha"), db)
        dept2 = create_department(_dept("Beta"), db)
        assert dept2.department_name == "Beta"


# ── List ───────────────────────────────────────────────────────────────────────

class TestShowDepartment:
    def test_returns_list(self, db):
        assert isinstance(show_department(db), list)

    def test_empty_when_no_departments(self, db):
        assert show_department(db) == []

    def test_contains_created_department(self, db, sample_department):
        names = [d.department_name for d in show_department(db)]
        assert "Engineering" in names

    def test_count_matches_created(self, db):
        create_department(_dept("Dept1"), db)
        create_department(_dept("Dept2"), db)
        assert len(show_department(db)) == 2


# ── Lookup by manager ──────────────────────────────────────────────────────────

class TestGetDepartmentByManagerId:
    def test_found_returns_department(self, db, sample_department, sample_employee):
        sample_department.manager_id = sample_employee.employee_id
        db.commit()
        result = get_department_by_manager_id(sample_employee.employee_id, db)
        assert result.department_id == sample_department.department_id

    def test_not_found_raises_400(self, db):
        with pytest.raises(HTTPException) as exc:
            get_department_by_manager_id(99999, db)
        assert exc.value.status_code == 400


# ── Delete ─────────────────────────────────────────────────────────────────────

class TestDeleteDepartment:
    def test_delete_existing_returns_message(self, db, sample_department):
        did = sample_department.department_id
        result = delete_department(did, db)
        assert "deleted" in result["message"].lower()

    def test_delete_removes_record(self, db, sample_department):
        did = sample_department.department_id
        delete_department(did, db)
        assert db.query(Department).filter(Department.department_id == did).first() is None

    def test_delete_nonexistent_raises_404(self, db):
        with pytest.raises(HTTPException) as exc:
            delete_department(99999, db)
        assert exc.value.status_code == 404


# ── Assign manager ─────────────────────────────────────────────────────────────

class TestAssignManager:
    def test_assigns_manager_successfully(self, db, sample_department, sample_employee):
        data = DepartmentUpdate()
        result = assign_manager(
            sample_employee.employee_id, sample_department.department_id, data, db
        )
        assert result.manager_id == sample_employee.employee_id

    def test_nonexistent_department_raises_400(self, db, sample_employee):
        with pytest.raises(HTTPException) as exc:
            assign_manager(sample_employee.employee_id, 99999, DepartmentUpdate(), db)
        assert exc.value.status_code == 400

    def test_nonexistent_manager_raises_404(self, db, sample_department):
        with pytest.raises(HTTPException) as exc:
            assign_manager(99999, sample_department.department_id, DepartmentUpdate(), db)
        assert exc.value.status_code == 404


# ── Get my department ──────────────────────────────────────────────────────────

class TestGetMyDepartment:
    def test_raises_400_when_user_has_no_department(self, db, admin_user):
        admin_user.department_id = None
        db.commit()
        with pytest.raises(HTTPException) as exc:
            get_my_department(admin_user, db)
        assert exc.value.status_code == 400

    def test_returns_correct_department(self, db, admin_user, sample_department):
        admin_user.department_id = sample_department.department_id
        db.commit()
        result = get_my_department(admin_user, db)
        assert result.department_id == sample_department.department_id

    def test_raises_404_when_assigned_department_deleted(self, db, admin_user, sample_department):
        admin_user.department_id = sample_department.department_id
        db.commit()
        db.delete(sample_department)
        db.commit()
        with pytest.raises(HTTPException) as exc:
            get_my_department(admin_user, db)
        assert exc.value.status_code == 404
