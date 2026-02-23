from datetime import date
from sqlalchemy.orm import Session
from app.data.repositories import shift_repository
from app.data.models.shifts import Shift, EmployeeShiftAssignment


def create_shift_service(db: Session, shift_data) -> Shift:
    shift = Shift(**shift_data.dict())
    return shift_repository.create_shift(db, shift)


def assign_shift_service(db: Session, assignment_data) -> EmployeeShiftAssignment:
    assignment = EmployeeShiftAssignment(**assignment_data.dict())
    return shift_repository.assign_shift(db, assignment)


def get_current_shift_service(db: Session, employee_id: str, target_date: date):
    return shift_repository.get_current_shift(db, employee_id, target_date)

def get_all_shifts_service(db: Session):
    return db.query(Shift).all()