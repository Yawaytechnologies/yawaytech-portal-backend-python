from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.data.models import Employee


class EmployeeRepository:
    def get_by_id(self, db: Session, id_: int) -> Optional[Employee]:
        return db.get(Employee, id_)

    def get_by_employee_id(self, db: Session, code: str) -> Optional[Employee]:
        stmt = select(Employee).where(Employee.employee_id == code)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, db: Session, email: str) -> Optional[Employee]:
        stmt = select(Employee).where(Employee.email == email)
        return db.execute(stmt).scalar_one_or_none()

    def create(self, db: Session, obj: Employee) -> Employee:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj: Employee) -> Employee:
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: Employee) -> None:
        db.delete(obj)
        db.commit()

    def list(
        self,
        db: Session,
        *,
        q: Optional[str],
        page: int,
        size: int,
        designation: Optional[str],
        marital_status: Optional[str],
    ) -> Tuple[List[Employee], int]:
        # defensive pagination
        page = max(1, int(page or 1))
        size = max(1, int(size or 10))

        stmt = select(Employee)

        # Normalize inputs
        q = (q or "").strip()
        designation = (designation or "").strip()
        marital_status = (marital_status or "").strip()

        if q:
            stmt = stmt.where(
                Employee.name.ilike(f"%{q}%") |
                Employee.employee_id.ilike(f"%{q}%")
            )

        if designation:
            # Use ilike in case values aren’t normalized in DB
            stmt = stmt.where(Employee.designation.ilike(designation))

        if marital_status:
            stmt = stmt.where(Employee.marital_status.ilike(marital_status))

        # Deterministic ordering for stable pagination
        stmt = stmt.order_by(Employee.id.desc())

        # Count total (wrap in subquery to preserve filters)
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(total_stmt).scalar() or 0

        # Page slice
        stmt = stmt.offset((page - 1) * size).limit(size)

        rows = db.execute(stmt).scalars().all()
        return rows, int(total)
