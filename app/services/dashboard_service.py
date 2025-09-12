from __future__ import annotations
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.data.models.add_employee import Employee, Department
from app.data.repositories.add_employee_repository import EmployeeRepository

class DashboardService:
    def __init__(self, repo: EmployeeRepository | None = None):
        self.repo = repo or EmployeeRepository()

    def get_employees(
        self,
        db: Session,
        department: Optional[Department],
        limit: int,
        offset: int,
    ) -> Tuple[List[Employee], int]:
        return self.repo.list_employees(db, department, limit, offset)
