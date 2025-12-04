from sqlalchemy.orm import Session
from app.schemas.shift import ShiftCreate, EmployeeShiftAssignmentCreate
from app.services import shift_service


def create_shift_controller(db: Session, shift: ShiftCreate):
    return shift_service.create_shift_service(db, shift)


def assign_shift_controller(db: Session, assignment: EmployeeShiftAssignmentCreate):
    return shift_service.assign_shift_service(db, assignment)


def get_current_shift_controller(db: Session, employee_id: str, target_date):
    return shift_service.get_current_shift_service(db, employee_id, target_date)
