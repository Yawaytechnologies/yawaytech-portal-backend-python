# app/controllers/add_employee_controller.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.services.add_employee_service import EmployeeService


class AddEmployeeController:
    def __init__(self, service: Optional[EmployeeService] = None):
        self.service = service or EmployeeService()

    def create(self, db: Session, payload: EmployeeCreate) -> EmployeeRead:
        try:
            return self.service.create_employee(db, payload)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))  # unique conflict

    def get(self, db: Session, id_: int) -> EmployeeRead:
        try:
            return self.service.get_employee(db, id_)
        except LookupError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    def list(
        self,
        db: Session,
        q: Optional[str],
        page: int,
        size: int,
        designation: Optional[str],
        marital_status: Optional[str],
    ):
        items, total = self.service.list_employees(
            db, q=q, page=page, size=size, designation=designation, marital_status=marital_status
        )
        return {"items": items, "total": total, "page": page, "size": size}

    def update(self, db: Session, id_: int, payload: EmployeeUpdate) -> EmployeeRead:
        try:
            return self.service.update_employee(db, id_, payload)
        except LookupError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    def delete(self, db: Session, id_: int):
        try:
            self.service.delete_employee(db, id_)
            return {"status": "deleted"}
        except LookupError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
