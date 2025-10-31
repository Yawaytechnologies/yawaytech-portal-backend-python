from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.security import verify_password, create_access_token
from app.data.repositories.employee_repository import EmployeeRepository


class EmployeeService:
    def __init__(self):
        self.repo = EmployeeRepository()

    def authenticate(self, db: Session, employee_id: str, password: str) -> str:
        employee = self.repo.get_by_employee_id(db, employee_id)
        if not employee:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(password, employee.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return create_access_token({"sub": employee.employee_id, "role": "employee"})
