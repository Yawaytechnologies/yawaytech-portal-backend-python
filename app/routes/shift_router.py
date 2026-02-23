from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.schemas.shift import (
    ShiftCreate,
    ShiftSchema,
    EmployeeShiftAssignmentCreate,
    EmployeeShiftAssignmentSchema,
)
from app.controllers import shift_controller
from app.data.db import get_db

router = APIRouter(prefix="/shifts", tags=["Shifts"])


@router.post("/", response_model=ShiftSchema)
def create_shift(shift: ShiftCreate, db: Session = Depends(get_db)):
    return shift_controller.create_shift_controller(db, shift)


@router.post("/assign", response_model=EmployeeShiftAssignmentSchema)
def assign_shift(assignment: EmployeeShiftAssignmentCreate, db: Session = Depends(get_db)):
    return shift_controller.assign_shift_controller(db, assignment)


@router.get("/employee/{employee_id}", response_model=ShiftSchema)
def get_current_shift(
    employee_id: str, target_date: date = date.today(), db: Session = Depends(get_db)
):
    shift = shift_controller.get_current_shift_controller(db, employee_id, target_date)
    if not shift:
        raise HTTPException(status_code=404, detail="No active shift found")
    return shift


@router.get("/allshits", response_model=list[ShiftSchema])
def get_all_shifts(db: Session = Depends(get_db)):
    return shift_controller.get_all_shifts_controller(db)
