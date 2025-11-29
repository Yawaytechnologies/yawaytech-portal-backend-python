from sqlalchemy.orm import Session
from app.data.models.shifts import Shift, EmployeeShiftAssignment

def create_shift(db: Session, shift: Shift) -> Shift:
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift

def assign_shift(db: Session, assignment: EmployeeShiftAssignment) -> EmployeeShiftAssignment:
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

def get_current_shift(db: Session, employee_id: str, date) -> Shift | None:
    return (
        db.query(Shift)
        .join(EmployeeShiftAssignment, Shift.id == EmployeeShiftAssignment.shift_id)
        .filter(EmployeeShiftAssignment.employee_id == employee_id)
        .filter(EmployeeShiftAssignment.effective_from <= date)
        .filter((EmployeeShiftAssignment.effective_to.is_(None)) | (EmployeeShiftAssignment.effective_to >= date))
        .first()
    )