from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.data.models.add_employee import Employee


class EmployeeRepository:
    def get_by_employee_id(self, db: Session, employee_id: str) -> Optional[Employee]:
        return db.execute(
            select(Employee).where(Employee.employee_id == employee_id)
        ).scalar_one_or_none()
