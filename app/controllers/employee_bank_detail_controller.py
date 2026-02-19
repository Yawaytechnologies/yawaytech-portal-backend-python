# app/controllers/employee_bank_detail_controller.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.employee_bank_detail import EmployeeBankDetailCreate, EmployeeBankDetailUpdate
from app.services import employee_bank_detail_service


def create_bank_detail(db: Session, data: EmployeeBankDetailCreate):
    return employee_bank_detail_service.create_bank_detail(db, data)


def get_bank_detail(db: Session, detail_id: int):
    detail = employee_bank_detail_service.get_bank_detail(db, detail_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Bank detail not found")
    return detail


def list_bank_details(db: Session):
    return employee_bank_detail_service.list_bank_details(db)


def update_bank_detail(db: Session, detail_id: int, updates: EmployeeBankDetailUpdate):
    detail = employee_bank_detail_service.update_bank_detail(db, detail_id, updates)
    if not detail:
        raise HTTPException(status_code=404, detail="Bank detail not found")
    return detail


def delete_bank_detail(db: Session, detail_id: int):
    success = employee_bank_detail_service.delete_bank_detail(db, detail_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bank detail not found")
    return {"detail": "Bank detail deleted"}
