from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.core.security import decode_token
from app.data.repositories.admin_repository import AdminRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")
repo = AdminRepository()

def get_current_admin(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        admin_id = payload.get("sub")
        if not admin_id:
            raise ValueError("missing sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    admin = repo.get_by_admin_id(db, admin_id)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Inactive or invalid admin")
    return admin

def require_admin(current = Depends(get_current_admin)):
    return current

def require_super_admin(current = Depends(get_current_admin)):
    if not getattr(current, "is_super_admin", False):
        raise HTTPException(status_code=403, detail="Super admin required")
    return current
