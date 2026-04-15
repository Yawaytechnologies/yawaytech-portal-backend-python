from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.data.models.add_employee import Employee
from app.data.models.employee_salary import EmployeeSalary
from app.data.models.monthly_summary import MonthlyEmployeeSummary
from app.services.employeee_salary_service import create_salary
from app.services.payroll_calculator_service import get_payroll_for_employee
from app.schemas.employee_salary import EmployeeSalaryCreate


class QueryStub:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


def test_get_payroll_for_employee_skips_policy_lookup_when_policy_tables_missing(monkeypatch):
    employee = SimpleNamespace(id=7, employee_id="YTPL503IT")
    salary_record = SimpleNamespace(
        id=3,
        employee_id=7,
        base_salary=25000.0,
        gross_salary=25000.0,
        payroll_policy_id=1,
    )

    db = MagicMock()
    db.query.side_effect = lambda model: {
        Employee: QueryStub(employee),
        EmployeeSalary: QueryStub(salary_record),
        MonthlyEmployeeSummary: QueryStub(None),
    }[model]

    monkeypatch.setattr(
        "app.services.payroll_calculator_service._payroll_policy_tables_exist",
        lambda db_session: False,
    )

    payroll = get_payroll_for_employee(db, "YTPL503IT", date(2026, 3, 1))

    assert payroll is not None
    assert payroll.base_salary == 25000.0
    assert payroll.gross_salary == 25000.0
    assert payroll.net_salary == 25000.0
    assert payroll.policy_id is None
    assert payroll.policy_name is None


def test_create_salary_skips_policy_lookup_when_policy_tables_missing(monkeypatch):
    employee = SimpleNamespace(id=7)
    db = MagicMock()
    db.query.side_effect = lambda model: {
        Employee: QueryStub(employee),
    }[model]

    monkeypatch.setattr(
        "app.services.employeee_salary_service._payroll_policy_tables_exist",
        lambda db_session: False,
    )

    payload = EmployeeSalaryCreate(
        employee_id=7,
        base_salary=32000.0,
        payroll_policy_id=1,
    )

    salary = create_salary(db, payload)

    assert salary.base_salary == 32000.0
    assert salary.gross_salary == 32000.0
    assert salary.payroll_policy_id == 1
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(salary)
