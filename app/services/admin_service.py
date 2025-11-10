import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.security import verify_password, hash_password, create_access_token
from app.data.models.admin import Admin
from app.data.repositories.admin_repository import AdminRepository


class AdminService:
    def __init__(self):
        self.repo = AdminRepository()

    def authenticate(self, db: Session, admin_id: str, password: str) -> str:
        admin = self.repo.get_by_admin_id(db, admin_id)
        if not admin or not admin.is_active:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(password, admin.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return create_access_token(
            {"sub": admin.admin_id, "is_super_admin": admin.is_super_admin}
        )

    def bootstrap_super_admin(
        self, db: Session, *, admin_id: str, password: str, bootstrap_token: str
    ) -> Admin:
        # Allow bootstrap if no admin exists or ENABLE_BOOTSTRAP is true
        enable_bootstrap = os.getenv("ENABLE_BOOTSTRAP", "false").lower() == "true"
        has_admin = self.repo.count_admins(db) >= 1
        if not enable_bootstrap and has_admin:
            raise HTTPException(status_code=403, detail="Bootstrap disabled")

        expected = os.getenv("ADMIN_BOOTSTRAP_TOKEN")
        if expected and expected != bootstrap_token:
            raise HTTPException(status_code=403, detail="Invalid bootstrap token")

        # single admin hard check
        if has_admin:
            raise HTTPException(status_code=400, detail="Only one admin is allowed")

        obj = Admin(
            admin_id=admin_id,
            password_hash=hash_password(password),
            is_active=True,
            is_super_admin=True,  # single admin ⇒ super by default
        )
        return self.repo.create(db, obj)
