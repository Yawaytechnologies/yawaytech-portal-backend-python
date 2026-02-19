# app/services/payroll_calculator_service.py
"""
Comprehensive payroll calculation service that integrates:
- Employee base salary
- Payroll policy rules (allowances/deductions)
- Attendance data (worked hours, overtime, absences)
- Monthly summary metrics
"""

from datetime import date
from typing import Optional, Dict, List, cast
from sqlalchemy.orm import Session

from app.data.models.add_employee import Employee
from app.data.models.employee_salary import EmployeeSalary
from app.data.models.payroll_policy import PayrollPolicy
from app.data.models.salary_breakdown import SalaryBreakdown
from app.data.models.monthly_summary import MonthlyEmployeeSummary

# Attendance models not required in this module


class PayrollCalculation:
    """Represents a single payroll calculation with detailed breakdown."""

    def __init__(self, employee_id: int, employee_code: str, month_start: date):
        self.employee_id = employee_id
        self.employee_code = employee_code
        self.month_start = month_start

        # Salary components
        self.base_salary: float = 0.0
        self.gross_salary: float = 0.0
        self.net_salary: float = 0.0

        # Attendance metrics
        self.present_days: int = 0
        self.total_work_days: int = 0
        self.worked_hours: float = 0.0
        self.overtime_hours: float = 0.0
        self.underwork_hours: float = 0.0
        self.paid_leave_hours: float = 0.0
        self.unpaid_leave_hours: float = 0.0

        # Breakdown details
        self.allowances: List[Dict] = []
        self.deductions: List[Dict] = []
        self.attendance_adjustments: List[Dict] = []

        # Policy info
        self.policy_name: Optional[str] = None
        self.policy_id: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "employee_id": self.employee_id,
            "employee_code": self.employee_code,
            "month_start": self.month_start.isoformat(),
            "salary": {
                "base": self.base_salary,
                "gross": self.gross_salary,
                "net": self.net_salary,
            },
            "attendance": {
                "present_days": self.present_days,
                "total_work_days": self.total_work_days,
                "worked_hours": round(self.worked_hours, 2),
                "expected_hours": round(self.total_work_days * 8, 2),  # 8 hours per day
                "overtime_hours": round(self.overtime_hours, 2),
                "underwork_hours": round(self.underwork_hours, 2),
                "paid_leave_hours": round(self.paid_leave_hours, 2),
                "unpaid_leave_hours": round(self.unpaid_leave_hours, 2),
            },
            "policy": {
                "id": self.policy_id,
                "name": self.policy_name,
            },
            "breakdown": {
                "allowances": self.allowances,
                "deductions": self.deductions,
                "attendance_adjustments": self.attendance_adjustments,
            },
        }


def get_payroll_for_employee(
    db: Session,
    employee_id: int,
    month_start: date,
) -> Optional[PayrollCalculation]:
    """
    Calculate payroll for a single employee for a given month.

    Args:
        db: Database session
        employee_id: Employee primary key
        month_start: First day of the month to calculate

    Returns:
        PayrollCalculation object with full breakdown, or None if employee not found
    """
    # 1. Fetch employee
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return None

    # 2. Fetch employee's current salary record
    salary_record = (
        db.query(EmployeeSalary)
        .filter(EmployeeSalary.employee_id == employee_id)
        .order_by(EmployeeSalary.id.desc())
        .first()
    )
    if not salary_record:
        return None

    # 3. Fetch monthly attendance summary
    summary = (
        db.query(MonthlyEmployeeSummary)
        .filter(
            MonthlyEmployeeSummary.employee_id == employee.employee_id,
            MonthlyEmployeeSummary.month_start == month_start,
        )
        .first()
    )

    # 4. Fetch policy
    policy = None
    if salary_record.payroll_policy_id:
        policy = (
            db.query(PayrollPolicy)
            .filter(PayrollPolicy.id == salary_record.payroll_policy_id)
            .first()
        )

    # Create calculation object
    calc = PayrollCalculation(
        employee_id=employee.id,
        employee_code=employee.employee_id,
        month_start=month_start,
    )

    calc.base_salary = salary_record.base_salary
    calc.policy_id = cast(Optional[int], policy.id) if policy else None
    calc.policy_name = cast(Optional[str], policy.name) if policy else None

    # Populate attendance metrics from summary
    if summary:
        calc.present_days = summary.present_days
        calc.total_work_days = summary.total_work_days
        calc.worked_hours = float(summary.total_worked_hours) if summary.total_worked_hours else 0.0
        calc.overtime_hours = float(summary.overtime_hours) if summary.overtime_hours else 0.0
        calc.underwork_hours = float(summary.underwork_hours) if summary.underwork_hours else 0.0
        calc.paid_leave_hours = float(summary.paid_leave_hours) if summary.paid_leave_hours else 0.0
        calc.unpaid_leave_hours = (
            float(summary.unpaid_leave_hours) if summary.unpaid_leave_hours else 0.0
        )

    # Calculate salary with policy rules and attendance adjustments
    if policy:
        _apply_policy_rules(calc, salary_record.base_salary, policy, summary)
    else:
        calc.gross_salary = salary_record.base_salary

    calc.net_salary = calc.gross_salary

    return calc


def get_payroll_for_all_employees(
    db: Session,
    month_start: date,
) -> List[PayrollCalculation]:
    """
    Calculate payroll for all employees for a given month.

    Args:
        db: Database session
        month_start: First day of the month to calculate

    Returns:
        List of PayrollCalculation objects
    """
    employees = db.query(Employee).all()
    results = []

    for employee in employees:
        payroll = get_payroll_for_employee(db, employee.id, month_start)
        if payroll:
            results.append(payroll)

    return results


def _apply_policy_rules(
    calc: PayrollCalculation,
    base_salary: float,
    policy: PayrollPolicy,
    summary: Optional[MonthlyEmployeeSummary],
) -> None:
    """
    Apply policy rules to calculate gross salary with breakdowns.
    Incorporates attendance metrics where applicable.
    """
    gross = base_salary

    if not policy.rules:
        calc.gross_salary = gross
        return

    for rule in policy.rules:
        if not rule.is_enabled:
            continue

        amount = 0.0
        applies_to = rule.applies_to.lower()

        # Determine amount based on rule type and attendance
        if summary and applies_to == "overtime":
            # Overtime pay: rule.value per hour
            overtime_hours = float(summary.overtime_hours) if summary.overtime_hours else 0.0
            amount = rule.value * overtime_hours
            if amount > 0:
                calc.attendance_adjustments.append(
                    {
                        "name": rule.rule_name,
                        "type": "overtime",
                        "hours": overtime_hours,
                        "rate": rule.value,
                        "amount": round(amount, 2),
                    }
                )

        elif summary and applies_to == "unpaid_leave":
            # Deduction for unpaid leave: rule.value per hour
            unpaid_hours = float(summary.unpaid_leave_hours) if summary.unpaid_leave_hours else 0.0
            amount = rule.value * unpaid_hours
            if amount > 0:
                calc.attendance_adjustments.append(
                    {
                        "name": rule.rule_name,
                        "type": "unpaid_leave_deduction",
                        "hours": unpaid_hours,
                        "rate": rule.value,
                        "amount": round(amount, 2),
                    }
                )

        elif summary and applies_to == "underwork":
            # Underwork penalty: rule.value per hour
            underwork_hours = float(summary.underwork_hours) if summary.underwork_hours else 0.0
            amount = rule.value * underwork_hours
            if amount > 0:
                calc.attendance_adjustments.append(
                    {
                        "name": rule.rule_name,
                        "type": "underwork_deduction",
                        "hours": underwork_hours,
                        "rate": rule.value,
                        "amount": round(amount, 2),
                    }
                )

        elif summary and applies_to == "attendance_bonus":
            # Attendance bonus: percentage/fixed if present_days >= threshold
            # Simple: fixed amount per present day
            present_days = summary.present_days if summary.present_days else 0
            amount = (
                (base_salary * rule.value / 100)
                if rule.is_percentage
                else (rule.value * present_days)
            )
            if amount > 0:
                calc.attendance_adjustments.append(
                    {
                        "name": rule.rule_name,
                        "type": "attendance_bonus",
                        "present_days": present_days,
                        "amount": round(amount, 2),
                    }
                )

        else:
            # Fixed allowance/deduction (percentage or flat)
            amount = (base_salary * rule.value / 100) if rule.is_percentage else rule.value

        # Update gross salary and track in lists
        rule_type_str = str(rule.rule_type)
        if "ALLOWANCE" in rule_type_str:
            gross += amount
            calc.allowances.append(
                {
                    "rule_name": rule.rule_name,
                    "is_percentage": rule.is_percentage,
                    "value": rule.value,
                    "amount": round(amount, 2),
                    "applies_to": rule.applies_to,
                }
            )
        elif "DEDUCTION" in rule_type_str:
            gross -= amount
            calc.deductions.append(
                {
                    "rule_name": rule.rule_name,
                    "is_percentage": rule.is_percentage,
                    "value": rule.value,
                    "amount": round(amount, 2),
                    "applies_to": rule.applies_to,
                }
            )

    calc.gross_salary = gross


def generate_salary_breakdown(
    db: Session,
    employee_id: int,
    month_start: date,
) -> Optional[EmployeeSalary]:
    """
    Generate/update salary record for an employee based on attendance and policy.
    Creates SalaryBreakdown entries for audit trail.

    Args:
        db: Database session
        employee_id: Employee primary key
        month_start: First day of month to generate salary for

    Returns:
        Updated EmployeeSalary record, or None if not found
    """
    payroll = get_payroll_for_employee(db, employee_id, month_start)
    if not payroll:
        return None

    salary = (
        db.query(EmployeeSalary)
        .filter(EmployeeSalary.employee_id == employee_id)
        .order_by(EmployeeSalary.id.desc())
        .first()
    )
    if not salary:
        return None

    # Update base and gross
    salary.base_salary = payroll.base_salary
    salary.gross_salary = payroll.gross_salary

    # Clear and regenerate breakdowns
    salary.breakdowns.clear()

    for allowance in payroll.allowances:
        breakdown = SalaryBreakdown(
            employee_salary_id=salary.id,
            rule_name=allowance["rule_name"],
            rule_type="ALLOWANCE",
            applies_to=allowance["applies_to"],
            amount=allowance["amount"],
        )
        salary.breakdowns.append(breakdown)

    for deduction in payroll.deductions:
        breakdown = SalaryBreakdown(
            employee_salary_id=salary.id,
            rule_name=deduction["rule_name"],
            rule_type="DEDUCTION",
            applies_to=deduction["applies_to"],
            amount=deduction["amount"],
        )
        salary.breakdowns.append(breakdown)

    for adjustment in payroll.attendance_adjustments:
        rule_type = (
            "ALLOWANCE"
            if adjustment.get("type") == "overtime" or adjustment.get("type") == "attendance_bonus"
            else "DEDUCTION"
        )
        breakdown = SalaryBreakdown(
            employee_salary_id=salary.id,
            rule_name=adjustment["name"],
            rule_type=rule_type,
            applies_to=adjustment.get("type", "attendance"),
            amount=adjustment["amount"],
        )
        salary.breakdowns.append(breakdown)

    db.commit()
    db.refresh(salary)
    return salary
