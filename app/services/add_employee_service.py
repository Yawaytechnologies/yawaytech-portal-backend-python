# app/services/add_employee_service.py
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

# app/services/add_employee_service.py
from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.data.repositories.add_employee_repository import EmployeeRepository
from app.data.models import Employee



def _enum_value_or_same(v: Optional[object]) -> Optional[str]:
    """
    Accepts an Enum, a str, or None and returns a plain str or None.
    This prevents AttributeError when payload fields are strings instead of Enums.
    """
    if v is None:
        return None
    return getattr(v, "value", v)  # Enum.value if Enum; else the value itself (e.g., str)


class EmployeeService:
    def __init__(self, repo: Optional[EmployeeRepository] = None):
        self.repo = repo or EmployeeRepository()
        self.logger = logging.getLogger(__name__)

    # --- Create ---

    def create_employee(self, db: Session, payload: EmployeeCreate) -> EmployeeRead:
        # Ensure unique constraints (employee_id & email)
        if self.repo.get_by_employee_id(db, payload.employee_id):
            self.logger.error(f"Create failed: Employee ID {payload.employee_id} already exists")
            raise ValueError("Employee ID already exists")
        if self.repo.get_by_email(db, payload.email):
            self.logger.error(f"Create failed: Email {payload.email} already exists")
            raise ValueError("Email already exists")

        obj = Employee(
            name=payload.name,
            parent_name=payload.parent_name,
            guardian_type=_enum_value_or_same(payload.guardian_type),
            employee_id=payload.employee_id,
            email=payload.email,
            mobile_number=payload.mobile_number,
            alternative_number=payload.alternative_number,
            designation=payload.designation,
            permanent_address=payload.permanent_address,
            marital_status=_enum_value_or_same(payload.marital_status),
            date_of_birth=payload.date_of_birth,
            date_of_joining=payload.date_of_joining,
            date_of_leaving=payload.date_of_leaving,
            uan_number=payload.uan_number,
        )
        created = self.repo.create(db, obj)
        self.logger.info(f"Created employee with ID {created.id} and employee_id {created.employee_id}")
        return EmployeeRead.model_validate(created)

    # --- Read ---

    def get_employee(self, db: Session, id_: int) -> EmployeeRead:
        obj = self.repo.get_by_id(db, id_)
        if not obj:
            self.logger.error(f"Get failed: Employee with id {id_} not found")
            raise LookupError("Employee not found")
        return EmployeeRead.model_validate(obj)

    def list_employees(
        self,
        db: Session,
        *,
        q: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        designation: Optional[str] = None,
        marital_status: Optional[str] = None,
    ) -> Tuple[List[EmployeeRead], int]:
        rows, total = self.repo.list(
            db, q=q, page=page, size=size, designation=designation, marital_status=marital_status
        )
        self.logger.info(
            "Listed employees with filters q=%s, designation=%s, marital_status=%s, page=%s, size=%s",
            q, designation, marital_status, page, size
        )
        return [EmployeeRead.model_validate(r) for r in rows], total

    # --- Update (PUT/PATCH) ---

    def update_employee(self, db: Session, id_: int, payload: EmployeeUpdate) -> EmployeeRead:
        obj = self.repo.get_by_id(db, id_)
        if not obj:
            self.logger.error(f"Update failed: Employee with id {id_} not found")
            raise LookupError("Employee not found")

        # Unique constraints if changing employee_id/email
        if payload.employee_id and payload.employee_id != obj.employee_id:
            if self.repo.get_by_employee_id(db, payload.employee_id):
                self.logger.error(f"Update failed: Employee ID {payload.employee_id} already exists")
                raise ValueError("Employee ID already exists")
            obj.employee_id = payload.employee_id

        if payload.email and payload.email != obj.email:
            if self.repo.get_by_email(db, payload.email):
                self.logger.error(f"Update failed: Email {payload.email} already exists")
                raise ValueError("Email already exists")
            obj.email = payload.email

        # Map remaining updates (only if provided)
        for field in [
            "name", "parent_name", "designation", "permanent_address",
            "mobile_number", "alternative_number", "uan_number",
            "date_of_birth", "date_of_joining", "date_of_leaving"
        ]:
            val = getattr(payload, field, None)
            if val is not None:
                setattr(obj, field, val)

        # Handle enum-or-string fields safely
        if payload.guardian_type is not None:
            obj.guardian_type = _enum_value_or_same(payload.guardian_type)

        if payload.marital_status is not None:
            obj.marital_status = _enum_value_or_same(payload.marital_status)

        obj.updated_at = datetime.utcnow()

        updated = self.repo.update(db, obj)
        self.logger.info(f"Updated employee with id {id_}")
        return EmployeeRead.model_validate(updated)

    # --- Delete ---

    def delete_employee(self, db: Session, id_: int) -> None:
        obj = self.repo.get_by_id(db, id_)
        if not obj:
            self.logger.error(f"Delete failed: Employee with id {id_} not found")
            raise LookupError("Employee not found")
        self.repo.delete(db, obj)
        self.logger.info(f"Deleted employee with id {id_}")
