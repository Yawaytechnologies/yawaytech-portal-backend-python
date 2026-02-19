from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.data.db import get_db
from app.controllers.add_employee_controller import AddEmployeeController
from app.data.models.add_employee import Department
from app.schemas.add_employee import EmployeeRead

router = APIRouter(prefix="/department", tags=["Department"])


def get_controller() -> AddEmployeeController:
    return AddEmployeeController()


@router.get("/{department_name}", response_model=List[EmployeeRead])
def get_department_employees(
    department_name: str,
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    """
    Get full details of all employees in a department.
    Department name should be one of: HR, IT, SALES, FINANCE, MARKETING
    """
    try:
        department = Department(department_name.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department name. Must be one of: {[d.value for d in Department]}",
        )

    employees = ctrl.get_by_department(db, department)
    return employees


@router.get("/employees/all", response_model=dict)
def get_all_employees_by_department(
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    """
    Get all employees grouped by department.
    Returns a dictionary where keys are department names and values are lists of employee details.
    """
    result = ctrl.get_all_employees_by_department(db)
    return result
