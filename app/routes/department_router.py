from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.data.db import get_db
from app.controllers.add_employee_controller import AddEmployeeController
from app.data.models.add_employee import Department

router = APIRouter(prefix="/department", tags=["Department"])


def get_controller() -> AddEmployeeController:
    return AddEmployeeController()


@router.get("/{department_name}")
def get_department_progress(
    department_name: str,
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    """
    Get progress metrics for all employees in a department.
    Department name should be one of: HR, IT, SALES, FINANCE, MARKETING
    """
    try:
        department = Department(department_name.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department name. Must be one of: {[d.value for d in Department]}",
        )

    progress = ctrl.get_department_progress(db, department)
    return progress
