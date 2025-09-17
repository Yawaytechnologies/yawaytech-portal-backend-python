# app/services/add_employee_service.py
from __future__ import annotations
from typing import List, Optional, Tuple, cast
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.security import hash_password
from app.data.models.add_employee import Employee
from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def create_employee(self, db: Session, payload: EmployeeCreate) -> Employee:
        exists_email = db.scalar(
            select(func.count()).select_from(Employee).where(Employee.email == payload.email)
        )
        if exists_email:
            raise ValueError("Email already exists")

        exists_empid = db.scalar(
            select(func.count())
            .select_from(Employee)
            .where(Employee.employee_id == payload.employee_id)
        )
        if exists_empid:
            raise ValueError("Employee ID already exists")

        # If you're on Pydantic v2, prefer payload.model_dump()
        data = payload.dict()
        data["password"] = hash_password(data.pop("password"))
        emp = Employee(**data)
        db.add(emp)
        db.commit()
        db.refresh(emp)
        return emp

    def get_employee(self, db: Session, id_: int) -> Optional[Employee]:
        return db.get(Employee, id_)

    def list_employees(
        self, db: Session, q: Optional[str], skip: int, limit: int
    ) -> Tuple[List[Employee], int]:
        stmt = select(Employee)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                (Employee.name.ilike(like))
                | (Employee.email.ilike(like))
                | (Employee.employee_id.ilike(like))
                | (Employee.designation.ilike(like))
            )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Employee.id.desc()).offset(skip).limit(limit)
        rows = db.scalars(stmt).all()

        # 🔑 mypy-safe: force concrete list[Employee]
        employees: List[Employee] = cast(List[Employee], list(rows))
        return employees, int(total)

    def update_employee(self, db: Session, id_: int, payload: EmployeeUpdate) -> Optional[Employee]:
        emp = db.get(Employee, id_)
        if not emp:
            return None

        data = payload.dict(
            exclude_unset=True
        )  # Pydantic v2: payload.model_dump(exclude_unset=True)

        if "password" in data:
            data["password"] = hash_password(data["password"])

        if "email" in data:
            dup = db.scalar(
                select(func.count())
                .select_from(Employee)
                .where(Employee.email == data["email"], Employee.id != id_)
            )
            if dup:
                raise ValueError("Email already exists")

        if "employee_id" in data:
            dup = db.scalar(
                select(func.count())
                .select_from(Employee)
                .where(Employee.employee_id == data["employee_id"], Employee.id != id_)
            )
            if dup:
                raise ValueError("Employee ID already exists")

        for k, v in data.items():
            setattr(emp, k, v)

        db.commit()
        db.refresh(emp)
        return emp

    def delete_employee(self, db: Session, id_: int) -> bool:
        emp = db.get(Employee, id_)
        if not emp:
            return False
        db.delete(emp)
        db.commit()
        return True
