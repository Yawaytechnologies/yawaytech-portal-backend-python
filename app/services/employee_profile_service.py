from __future__ import annotations
import logging
from collections import OrderedDict
from sqlalchemy.orm import Session
from fastapi import UploadFile
from datetime import datetime, timezone

from app.core.config import settings
from app.core.image_utils import optimize_image_for_storage, validate_image_upload
from app.core.supabase_client import get_supabase
from app.data.repositories.employee_repository import EmployeeRepository
from app.data.repositories.employee_profile_repository import EmployeeProfileRepo

logger = logging.getLogger(__name__)


class EmployeeProfileService:
    def __init__(self):
        self.emp_repo = EmployeeRepository()
        self.profile_repo = EmployeeProfileRepo()
        self._signed_url_cache: OrderedDict[tuple[str, str], tuple[str, float]] = OrderedDict()

    async def upload_profile_image(self, db: Session, employee_id: str, file: UploadFile):
        # 1) validate employee exists
        emp = self.emp_repo.get_by_employee_id(db, employee_id)
        if not emp:
            raise ValueError("Employee not found")

        # 2) validate file
        data = await file.read()
        validate_image_upload(
            data,
            file.content_type or "",
            max_bytes=settings.PROFILE_IMAGE_MAX_BYTES,
        )
        optimized_data = optimize_image_for_storage(
            data,
            max_dimension=settings.OPTIMIZED_PROFILE_MAX_DIMENSION,
            quality=settings.OPTIMIZED_PROFILE_JPEG_QUALITY,
        )

        # 3) build storage path (unique)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bucket = settings.SUPABASE_PROFILE_BUCKET
        path = f"employees/{employee_id}/profile_{ts}.jpg"

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
                optimized_data,
                file_options={
                    "content-type": "image/jpeg",
                    "cache-control": "31536000",
                    "upsert": "true",
                },
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
            mime="image/jpeg",
            size=len(optimized_data),
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
        now = datetime.now(timezone.utc).timestamp()
        cache_key = (bucket, path)
        cached = self._signed_url_cache.get(cache_key)
        if cached and cached[1] > now:
            self._signed_url_cache.move_to_end(cache_key)
            return cached[0]

        signed = supabase.storage.from_(bucket).create_signed_url(
            path, settings.SIGNED_URL_EXPIRE_SECONDS
        )
        # signed is usually dict: {"signedURL": "..."} in many versions
        url = str(signed.get("signedURL") or signed.get("signed_url") or "")
        expires_at = now + max(0, settings.SIGNED_URL_EXPIRE_SECONDS - 30)
        self._signed_url_cache[cache_key] = (url, expires_at)
        if len(self._signed_url_cache) > 512:
            self._signed_url_cache.popitem(last=False)
        return url
