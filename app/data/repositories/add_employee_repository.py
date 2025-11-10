# app/data/repositories/add_employee_repository.py
from __future__ import annotations

from typing import Optional, Tuple, List, cast
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from app.data.models.add_employee import Employee, Department


class EmployeeRepository:
    def update(self, db: Session, obj: Employee) -> Employee:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: Employee) -> None:
        db.delete(obj)
        db.commit()

    def get_by_employee_id(self, db: Session, code: str) -> Optional[Employee]:
        return db.execute(
            select(Employee).where(Employee.employee_id == code)
        ).scalar_one_or_none()

    # def get_by_email(self, db: Session, email: str) -> Optional[Employee]:
    #     return db.execute(select(Employee).where(Employee.email == email)).scalar_one_or_none()

    # def get_by_phone(self, db: Session, phone: str) -> Optional[Employee]:
    #     return db.execute(select(Employee).where(Employee.phone == phone)).scalar_one_or_none()

    def list(
        self,
        db: Session,
        *,
        q: Optional[str],
        page: int,
        size: int,
        department: Optional[str | Department] = None,
    ) -> Tuple[List[Employee], int]:
        stmt = select(Employee)

        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Employee.email.ilike(like),
                    Employee.employee_id.ilike(like),
                )
            )

        if department:
            stmt = stmt.where(Employee.department == department)

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        rows = (
            db.execute(
                stmt.order_by(Employee.id.desc()).offset((page - 1) * size).limit(size)
            )
            .scalars()
            .all()
        )

        employees: List[Employee] = cast(List[Employee], list(rows))
        return employees, int(total)

    # Optional helper to mimic old signature (uses offset/limit)
    def list_employees(
        self,
        db: Session,
        department: Optional[Department] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Employee], int]:
        page = (offset // max(1, limit)) + 1
        return self.list(
            db,
            q=None,
            page=page,
            size=limit,
            department=department,
        )
