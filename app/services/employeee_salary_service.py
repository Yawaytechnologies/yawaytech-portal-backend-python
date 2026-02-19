# app/services/employee_salary_service.py
from typing import Optional
from sqlalchemy.orm import Session
from app.data.models.employee_salary import EmployeeSalary
from app.data.models.payroll_policy import PayrollPolicy
from app.data.models.salary_breakdown import SalaryBreakdown
from app.data.models.add_employee import Employee
from app.schemas.employee_salary import EmployeeSalaryCreate, EmployeeSalaryUpdate


def calculate_gross_with_breakdown(base_salary: float, policy: Optional[PayrollPolicy]):
    gross = base_salary
    breakdowns = []

    if policy:
        for rule in policy.rules:
            if not rule.is_enabled:
                continue
            amount = (base_salary * rule.value / 100) if rule.is_percentage else rule.value
            breakdowns.append(
                {
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "amount": amount,
                    "applies_to": rule.applies_to,
                }
            )
            if rule.rule_type == "ALLOWANCE":
                gross += amount
            elif rule.rule_type == "DEDUCTION":
                gross -= amount

    return gross, breakdowns


def create_salary(db: Session, data: EmployeeSalaryCreate):
    # Query employee by id
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise ValueError(f"Employee with id {data.employee_id} not found")

    policy = db.query(PayrollPolicy).filter(PayrollPolicy.id == data.payroll_policy_id).first()
    gross, breakdowns = calculate_gross_with_breakdown(data.base_salary, policy)

    salary = EmployeeSalary(
        employee_id=employee.id,
        base_salary=data.base_salary,
        gross_salary=gross,
        payroll_policy_id=data.payroll_policy_id,
    )
    db.add(salary)
    db.flush()  # ensures salary.id is available

    for b in breakdowns:
        db.add(SalaryBreakdown(employee_salary_id=salary.id, **b))

    db.commit()
    db.refresh(salary)
    return salary


def update_salary(db: Session, salary_id: int, updates: EmployeeSalaryUpdate):
    salary = db.query(EmployeeSalary).filter(EmployeeSalary.id == salary_id).first()
    if not salary:
        return None

    if updates.base_salary is not None:
        salary.base_salary = updates.base_salary
    if updates.payroll_policy_id is not None:
        salary.payroll_policy_id = updates.payroll_policy_id

    policy = db.query(PayrollPolicy).filter(PayrollPolicy.id == salary.payroll_policy_id).first()
    gross, breakdowns = calculate_gross_with_breakdown(salary.base_salary, policy)
    salary.gross_salary = gross

    salary.breakdowns.clear()
    db.flush()
    for b in breakdowns:
        db.add(SalaryBreakdown(employee_salary_id=salary.id, **b))

    db.commit()
    db.refresh(salary)
    return salary


def get_salary(db: Session, salary_id: int):
    return db.query(EmployeeSalary).filter(EmployeeSalary.id == salary_id).first()


def list_salaries(db: Session):
    return db.query(EmployeeSalary).all()


def delete_salary(db: Session, salary_id: int):
    salary = db.query(EmployeeSalary).filter(EmployeeSalary.id == salary_id).first()
    if salary:
        db.delete(salary)
        db.commit()
        return True
    return False
