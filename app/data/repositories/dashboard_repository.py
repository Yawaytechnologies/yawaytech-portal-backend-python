from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.data.models.add_employee import Employee, Department


class EmployeeRepository:
    """DB-facing queries only (no business logic)."""

    def list_by_department(
        self,
        db: Session,
        department: Department,
        limit: int = 20,
        offset: int = 0,
        q: Optional[str] = None,
    ) -> Tuple[list[Employee], int]:
        # Base filter
        stmt = select(Employee).where(Employee.department == department)

        # Quick text search (name, email, employee_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Employee.name.ilike(like),
                    Employee.email.ilike(like),
                    Employee.employee_id.ilike(like),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Page slice
        stmt = stmt.order_by(Employee.name.asc()).limit(limit).offset(offset)
        rows = list(db.execute(stmt).scalars().all())
        return rows, total
