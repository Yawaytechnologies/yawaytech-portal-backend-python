# app/routes/payroll_calculator_router.py
"""
API endpoints for payroll calculations and examination.
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.data.db import SessionLocal
from app.services.payroll_calculator_service import (
    get_payroll_for_employee,
    get_payroll_for_all_employees,
    generate_salary_breakdown,
)


router = APIRouter(prefix="/api/payroll", tags=["payroll"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/calculation/employee/{employee_id}")
async def get_employee_payroll(
    employee_id: int,
    month_start: date = Query(..., description="First day of month (YYYY-MM-01)"),
    db: Session = Depends(get_db),
):
    """
    Calculate payroll for a single employee for a given month.

    Returns detailed breakdown including:
    - Base salary and gross salary
    - Attendance metrics (present days, worked hours, overtime, etc.)
    - Policy rules applied (allowances & deductions)
    - Attendance-based adjustments (overtime pay, absence deductions)
    """
    payroll = get_payroll_for_employee(db, employee_id, month_start)
    if not payroll:
        raise HTTPException(status_code=404, detail="Employee or salary record not found")

    return payroll.to_dict()


@router.get("/calculation/all")
async def get_all_employees_payroll(
    month_start: date = Query(..., description="First day of month (YYYY-MM-01)"),
    db: Session = Depends(get_db),
):
    """
    Calculate payroll for all employees for a given month.

    Returns list of payroll calculations with full breakdowns.
    """
    payrolls = get_payroll_for_all_employees(db, month_start)
    return [p.to_dict() for p in payrolls]


@router.post("/generate/employee/{employee_id}")
async def generate_employee_salary(
    employee_id: int,
    month_start: date = Query(..., description="First day of month (YYYY-MM-01)"),
    db: Session = Depends(get_db),
):
    """
    Generate/update salary record with full breakdown for an employee.

    This endpoint:
    1. Calculates payroll for the given month
    2. Updates the EmployeeSalary record
    3. Creates detailed SalaryBreakdown entries for audit trail

    Returns the updated EmployeeSalary record.
    """
    salary = generate_salary_breakdown(db, employee_id, month_start)
    if not salary:
        raise HTTPException(status_code=404, detail="Employee or salary record not found")

    return {
        "id": salary.id,
        "employee_id": salary.employee_id,
        "base_salary": salary.base_salary,
        "gross_salary": salary.gross_salary,
        "payroll_policy_id": salary.payroll_policy_id,
        "breakdowns": [
            {
                "rule_name": b.rule_name,
                "rule_type": b.rule_type,
                "applies_to": b.applies_to,
                "amount": b.amount,
            }
            for b in salary.breakdowns
        ],
    }


@router.post("/generate/all")
async def generate_all_employees_salaries(
    month_start: date = Query(..., description="First day of month (YYYY-MM-01)"),
    db: Session = Depends(get_db),
):
    """
    Generate/update salary records for all employees for a given month.

    Returns summary of generated records.
    """
    from app.data.models.add_employee import Employee

    employees = db.query(Employee).all()
    results = []
    errors = []

    for employee in employees:
        try:
            salary = generate_salary_breakdown(db, employee.id, month_start)
            if salary:
                results.append(
                    {
                        "employee_id": employee.id,
                        "employee_code": employee.employee_id,
                        "gross_salary": salary.gross_salary,
                        "status": "success",
                    }
                )
            else:
                errors.append(
                    {
                        "employee_id": employee.id,
                        "error": "Salary record not found",
                    }
                )
        except Exception as e:
            errors.append(
                {
                    "employee_id": employee.id,
                    "error": str(e),
                }
            )

    return {
        "month": month_start.isoformat(),
        "generated": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
