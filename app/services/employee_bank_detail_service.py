# app/services/employee_bank_detail_service.py
from sqlalchemy.orm import Session
from app.data.models.employee_bank_detail import EmployeeBankDetail
from app.schemas.employee_bank_detail import EmployeeBankDetailCreate, EmployeeBankDetailUpdate


def create_bank_detail(db: Session, data: EmployeeBankDetailCreate):
    detail = EmployeeBankDetail(**data.dict())
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail


def get_bank_detail(db: Session, detail_id: int):
    return db.query(EmployeeBankDetail).filter(EmployeeBankDetail.id == detail_id).first()


def list_bank_details(db: Session):
    return db.query(EmployeeBankDetail).all()


def update_bank_detail(db: Session, detail_id: int, updates: EmployeeBankDetailUpdate):
    detail = db.query(EmployeeBankDetail).filter(EmployeeBankDetail.id == detail_id).first()
    if not detail:
        return None
    for k, v in updates.dict(exclude_unset=True).items():
        setattr(detail, k, v)
    db.commit()
    db.refresh(detail)
    return detail


def delete_bank_detail(db: Session, detail_id: int):
    detail = db.query(EmployeeBankDetail).filter(EmployeeBankDetail.id == detail_id).first()
    if detail:
        db.delete(detail)
        db.commit()
        return True
    return False
