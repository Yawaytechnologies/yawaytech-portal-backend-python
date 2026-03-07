# app/services/employee_bank_detail_service.py
from sqlalchemy.orm import Session
from app.data.models.employee_bank_detail import EmployeeBankDetail
from app.data.models.add_employee import Employee
from app.schemas.employee_bank_detail import (
    EmployeeBankDetailCreate,
    EmployeeBankDetailUpdate,
)


def _to_read_dict(detail: EmployeeBankDetail, employee_code: str | None):
    """Map DB row -> API response dict (employee_id becomes code like YTPL503IT)."""
    return {
        "id": detail.id,
        "employee_id": employee_code,  # ✅ return employees.employee_id (YTPL503IT)
        "bank_name": detail.bank_name,
        "account_number": detail.account_number,
        "ifsc_code": detail.ifsc_code,
        "branch_name": detail.branch_name,
    }


def create_bank_detail(db: Session, data: EmployeeBankDetailCreate):
    detail = EmployeeBankDetail(**data.dict())
    db.add(detail)
    db.commit()
    db.refresh(detail)

    emp_employee_id = (
        db.query(Employee.employee_id).filter(Employee.id == detail.employee_id).scalar()
    )
    return _to_read_dict(detail, emp_employee_id)


def get_bank_detail(db: Session, employee_id: str):
    row = (
        db.query(EmployeeBankDetail, Employee.employee_id)
        .join(Employee, EmployeeBankDetail.employee_id == Employee.id)
        .filter(Employee.employee_id == employee_id)
        .first()
    )
    if not row:
        return None

    detail, emp_employee_id = row
    return _to_read_dict(detail, emp_employee_id)


def list_bank_details(db: Session):
    rows = (
        db.query(EmployeeBankDetail, Employee.employee_id)
        .join(Employee, EmployeeBankDetail.employee_id == Employee.id)
        .all()
    )

    return [_to_read_dict(detail, emp_employee_id) for detail, emp_employee_id in rows]


def update_bank_detail(db: Session, employee_id: str, updates: EmployeeBankDetailUpdate):
    detail = db.query(EmployeeBankDetail).filter(Employee.employee_id == employee_id).first()
    if not detail:
        return None

    for k, v in updates.dict(exclude_unset=True).items():
        setattr(detail, k, v)

    db.commit()
    db.refresh(detail)

    emp_employee_id = (
        db.query(Employee.employee_id).filter(Employee.id == detail.employee_id).scalar()
    )
    return _to_read_dict(detail, emp_employee_id)


def delete_bank_detail(db: Session, employee_id: str):
    detail = db.query(EmployeeBankDetail).filter(Employee.employee_id == employee_id).first()
    if detail:
        db.delete(detail)
        db.commit()
        return True
    return False
