from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.services.employee_profile_service import EmployeeProfileService


class EmployeeProfileController:
    def __init__(self):
        self.svc = EmployeeProfileService()

    async def upload_profile_image(self, db: Session, employee_id: str, file: UploadFile):
        return await self.svc.upload_profile_image(db, employee_id, file)

    def get_profile(self, db: Session, employee_id: str):
        return self.svc.get_profile(db, employee_id)
