from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.schemas.admin import AdminLogin, TokenOut, BootstrapCreate
from app.services.admin_service import AdminService
from app.core.deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])
svc = AdminService()


@router.post("/login", response_model=TokenOut)
def login(payload: AdminLogin, db: Session = Depends(get_db)):
    token = svc.authenticate(db, payload.admin_id, payload.password)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/bootstrap", response_model=dict)
def bootstrap(payload: BootstrapCreate, db: Session = Depends(get_db)):
    admin = svc.bootstrap_super_admin(db, **payload.model_dump())
    return {
        "id": admin.id,
        "admin_id": admin.admin_id,
        "is_super_admin": admin.is_super_admin,
    }


@router.get("/me", dependencies=[Depends(require_admin)], response_model=dict)
def me(current=Depends(require_admin)):
    return {
        "admin_id": current.admin_id,
        "is_super_admin": current.is_super_admin,
        "is_active": current.is_active,
    }
