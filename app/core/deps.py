from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.core.security import decode_token
from app.data.repositories.admin_repository import AdminRepository
from app.data.repositories.employee_repository import EmployeeRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")
admin_repo = AdminRepository()
employee_repo = EmployeeRepository()


def get_current_admin(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    try:
        payload = decode_token(token)
        admin_id = payload.get("sub")
        if not admin_id:
            raise ValueError("missing sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    admin = admin_repo.get_by_admin_id(db, admin_id)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Inactive or invalid admin")
    return admin


def require_admin(current=Depends(get_current_admin)):
    return current


def require_super_admin(current=Depends(get_current_admin)):
    if not getattr(current, "is_super_admin", False):
        raise HTTPException(status_code=403, detail="Super admin required")
    return current


def get_current_employee(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    try:
        payload = decode_token(token)
        employee_id = payload.get("sub")
        role = payload.get("role")
        if not employee_id or role != "employee":
            raise ValueError("missing sub or invalid role")
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    employee = employee_repo.get_by_employee_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid employee")
    return employee


def require_employee(current=Depends(get_current_employee)):
    return current
