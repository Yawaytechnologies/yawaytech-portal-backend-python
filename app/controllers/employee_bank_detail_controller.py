# app/controllers/employee_bank_detail_controller.py
from sqlalchemy.orm import Session
from app.schemas.employee_bank_detail import (
    EmployeeBankDetailCreate,
    EmployeeBankDetailUpdate,
)
from app.services import employee_bank_detail_service


def create_bank_detail(db: Session, data: EmployeeBankDetailCreate):
    return employee_bank_detail_service.create_bank_detail(db, data)


def get_all_bank_details(db: Session):
    return employee_bank_detail_service.get_all_bank_details(db)


def get_bank_detail_by_employee_id(db: Session, employee_id: str):
    return employee_bank_detail_service.get_bank_detail_by_employee_id(db, employee_id)


def update_bank_detail(db: Session, employee_id: str, data: EmployeeBankDetailUpdate):
    return employee_bank_detail_service.update_bank_detail(db, employee_id, data)


def delete_bank_detail(db: Session, employee_id: str):
    return employee_bank_detail_service.delete_bank_detail(db, employee_id)