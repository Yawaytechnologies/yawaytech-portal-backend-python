from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.data.models.employee_profile import EmployeeProfile


class EmployeeProfileRepo:
    def get_by_employee_id(self, db: Session, employee_id: str) -> EmployeeProfile | None:
        return db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == employee_id).first()

    def upsert_profile_image(
        self,
        db: Session,
        employee_id: str,
        bucket: str,
        path: str,
        mime: str | None,
        size: int | None,
    ) -> EmployeeProfile:
        row = self.get_by_employee_id(db, employee_id)
        if not row:
            row = EmployeeProfile(employee_id=employee_id)
            db.add(row)

        row.profile_bucket = bucket  # type: ignore[assignment]
        row.profile_path = path  # type: ignore[assignment]
        row.profile_mime = mime  # type: ignore[assignment]
        row.profile_size = size  # type: ignore[assignment]
        row.profile_updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]

        db.commit()
        db.refresh(row)
        return row
