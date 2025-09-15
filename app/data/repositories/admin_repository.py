from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.data.models.admin import Admin


class AdminRepository:
    def get_by_admin_id(self, db: Session, admin_id: str) -> Optional[Admin]:
        return db.execute(select(Admin).where(Admin.admin_id == admin_id)).scalar_one_or_none()

    def count_admins(self, db: Session) -> int:
        return db.execute(select(func.count()).select_from(Admin)).scalar_one()

    def create(self, db: Session, admin: Admin) -> Admin:
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
