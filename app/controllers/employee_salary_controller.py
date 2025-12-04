# app/controllers/employee_salary_controller.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.employee_salary import EmployeeSalaryCreate, EmployeeSalaryUpdate
from app.services import employeee_salary_service


def create_salary(db: Session, data: EmployeeSalaryCreate):
    return employeee_salary_service.create_salary(db, data)


def get_salary(db: Session, salary_id: int):
    salary = employeee_salary_service.get_salary(db, salary_id)
    if not salary:
        raise HTTPException(status_code=404, detail="Salary not found")
    return salary


def list_salaries(db: Session):
    return employeee_salary_service.list_salaries(db)


def update_salary(db: Session, salary_id: int, updates: EmployeeSalaryUpdate):
    salary = employeee_salary_service.update_salary(db, salary_id, updates)
    if not salary:
        raise HTTPException(status_code=404, detail="Salary not found")
    return salary


def delete_salary(db: Session, salary_id: int):
    success = employeee_salary_service.delete_salary(db, salary_id)
    if not success:
        raise HTTPException(status_code=404, detail="Salary not found")
    return {"detail": "Salary deleted"}
