# app/routers/employee_salary_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.schemas.employee_salary import (
    EmployeeSalaryCreate,
    EmployeeSalaryRead,
    EmployeeSalaryUpdate,
)
from app.controllers import employee_salary_controller

router = APIRouter(prefix="/salaries", tags=["Employee Salaries"])


@router.post("/", response_model=EmployeeSalaryRead)
def create_salary(data: EmployeeSalaryCreate, db: Session = Depends(get_db)):
    return employee_salary_controller.create_salary(db, data)


@router.get("/{salary_id}", response_model=EmployeeSalaryRead)
def get_salary(salary_id: int, db: Session = Depends(get_db)):
    return employee_salary_controller.get_salary(db, salary_id)


@router.get("/", response_model=list[EmployeeSalaryRead])
def list_salaries(db: Session = Depends(get_db)):
    return employee_salary_controller.list_salaries(db)


@router.put("/{salary_id}", response_model=EmployeeSalaryRead)
def update_salary(salary_id: int, updates: EmployeeSalaryUpdate, db: Session = Depends(get_db)):
    return employee_salary_controller.update_salary(db, salary_id, updates)


@router.delete("/{salary_id}")
def delete_salary(salary_id: int, db: Session = Depends(get_db)):
    return employee_salary_controller.delete_salary(db, salary_id)
