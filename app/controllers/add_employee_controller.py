# app/controllers/add_employee_controller.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.services.add_employee_service import EmployeeService


class AddEmployeeController:
    def __init__(self, service: EmployeeService | None = None):
        self.service = service or EmployeeService()

    def create(self, db: Session, payload: EmployeeCreate) -> EmployeeRead:
        emp = self.service.create_employee(db, payload)
        return EmployeeRead.model_validate(emp)

    def get_one(self, db: Session, employee_id: str) -> Optional[EmployeeRead]:
        emp = self.service.get_employee(db, employee_id)
        return EmployeeRead.model_validate(emp) if emp else None

    def list_many(
        self,
        db: Session,
        q: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> tuple[list[EmployeeRead], int]:
        rows, total = self.service.list_employees(db, q=q, skip=skip, limit=limit)
        return [EmployeeRead.model_validate(r) for r in rows], total

    def update(
        self, db: Session, employee_id: str, payload: EmployeeUpdate
    ) -> Optional[EmployeeRead]:
        emp = self.service.update_employee(db, employee_id, payload)
        return EmployeeRead.model_validate(emp) if emp else None

    def delete(self, db: Session, employee_id: str) -> bool:
        return self.service.delete_employee(db, employee_id)
