# app/routes/employee_bank_detail_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.controllers import employee_bank_detail_controller
from app.schemas.employee_bank_detail import (
    EmployeeBankDetailCreate,
    EmployeeBankDetailUpdate,
    EmployeeBankDetailRead,
)

router = APIRouter(prefix="/bank-details", tags=["Bank Details"])


@router.post("/", response_model=EmployeeBankDetailRead)
def create_bank_detail(data: EmployeeBankDetailCreate, db: Session = Depends(get_db)):
    return employee_bank_detail_controller.create_bank_detail(db, data)


@router.get("/", response_model=list[EmployeeBankDetailRead])
def list_bank_details(db: Session = Depends(get_db)):
    return employee_bank_detail_controller.list_bank_details(db)


@router.get("/{employee_id}", response_model=EmployeeBankDetailRead)
def get_bank_detail_by_employee_id(employee_id: str, db: Session = Depends(get_db)):
    return employee_bank_detail_controller.get_bank_detail_by_employee_id(db, employee_id)


@router.put("/{employee_id}", response_model=EmployeeBankDetailRead)
def update_bank_detail(
    employee_id: str,
    data: EmployeeBankDetailUpdate,
    db: Session = Depends(get_db),
):
    return employee_bank_detail_controller.update_bank_detail(db, employee_id, data)


@router.delete("/{employee_id}")
def delete_bank_detail(employee_id: str, db: Session = Depends(get_db)):
    return employee_bank_detail_controller.delete_bank_detail(db, employee_id)