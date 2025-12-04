# app/routers/employee_bank_detail_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.schemas.employee_bank_detail import (
    EmployeeBankDetailCreate,
    EmployeeBankDetailRead,
    EmployeeBankDetailUpdate,
)
from app.controllers import employee_bank_detail_controller

router = APIRouter(prefix="/bank-details", tags=["Employee Bank Details"])


@router.post("/", response_model=EmployeeBankDetailRead)
def create_bank_detail(data: EmployeeBankDetailCreate, db: Session = Depends(get_db)):
    return employee_bank_detail_controller.create_bank_detail(db, data)


@router.get("/{detail_id}", response_model=EmployeeBankDetailRead)
def get_bank_detail(detail_id: int, db: Session = Depends(get_db)):
    return employee_bank_detail_controller.get_bank_detail(db, detail_id)


@router.get("/", response_model=list[EmployeeBankDetailRead])
def list_bank_details(db: Session = Depends(get_db)):
    return employee_bank_detail_controller.list_bank_details(db)


@router.put("/{detail_id}", response_model=EmployeeBankDetailRead)
def update_bank_detail(
    detail_id: int, updates: EmployeeBankDetailUpdate, db: Session = Depends(get_db)
):
    return employee_bank_detail_controller.update_bank_detail(db, detail_id, updates)


@router.delete("/{detail_id}")
def delete_bank_detail(detail_id: int, db: Session = Depends(get_db)):
    return employee_bank_detail_controller.delete_bank_detail(db, detail_id)
