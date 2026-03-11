from __future__ import annotations
import logging
from sqlalchemy.orm import Session
from fastapi import UploadFile
from datetime import datetime, timezone

from app.core.config import settings
from app.core.supabase_client import get_supabase
from app.data.repositories.employee_repository import EmployeeRepository
from app.data.repositories.employee_profile_repository import EmployeeProfileRepo

logger = logging.getLogger(__name__)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 3 * 1024 * 1024  # 3MB


class EmployeeProfileService:
    def __init__(self):
        self.emp_repo = EmployeeRepository()
        self.profile_repo = EmployeeProfileRepo()

    async def upload_profile_image(self, db: Session, employee_id: str, file: UploadFile):
        # 1) validate employee exists
        emp = self.emp_repo.get_by_employee_id(db, employee_id)
        if not emp:
            raise ValueError("Employee not found")

        # 2) validate file
        content_type = (file.content_type or "").lower()
        if content_type not in ALLOWED_MIME:
            raise ValueError("Only JPG/PNG/WEBP allowed")

        data = await file.read()
        if not data:
            raise ValueError("Empty file")
        if len(data) > MAX_BYTES:
            raise ValueError("Image too large (max 3MB)")

        # 3) build storage path (unique)
        ext = (
            "jpg"
            if content_type == "image/jpeg"
            else ("png" if content_type == "image/png" else "webp")
        )
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bucket = settings.SUPABASE_PROFILE_BUCKET
        path = f"employees/{employee_id}/profile_{ts}.{ext}"

        supabase = get_supabase()

        # 4) delete old image (optional best practice)
        existing = self.profile_repo.get_by_employee_id(db, employee_id)
        if existing and existing.profile_bucket and existing.profile_path:
            try:
                supabase.storage.from_(existing.profile_bucket).remove([existing.profile_path])
            except Exception:
                # don't fail upload if delete fails
                pass

        # 5) upload to Supabase
        try:
            res = supabase.storage.from_(bucket).upload(
                path,
                data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            logger.info(f"Supabase upload response: {res}")
        except Exception as e:
            logger.error(f"Supabase upload failed: {str(e)}")
            raise ValueError(f"Upload to storage failed: {str(e)}")

        # 6) save metadata in DB
        row = self.profile_repo.upsert_profile_image(
            db=db,
            employee_id=employee_id,
            bucket=bucket,
            path=path,
            mime=content_type,
            size=len(data),
        )

        # 7) return URL for UI
        url = self._build_image_url(bucket, path)
        return row, url

    def get_profile(self, db: Session, employee_id: str):
        row = self.profile_repo.get_by_employee_id(db, employee_id)
        if not row:
            return None, None
        url = None
        if row.profile_bucket and row.profile_path:
            url = self._build_image_url(row.profile_bucket, row.profile_path)
        return row, url

    def _build_image_url(self, bucket: str, path: str) -> str:
        supabase = get_supabase()

        if settings.SUPABASE_BUCKET_PUBLIC:
            # public bucket URL format:
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"

        # private bucket -> signed URL
        signed = supabase.storage.from_(bucket).create_signed_url(
            path, settings.SIGNED_URL_EXPIRE_SECONDS
        )
        # signed is usually dict: {"signedURL": "..."} in many versions
        return str(signed.get("signedURL") or signed.get("signed_url") or "")
