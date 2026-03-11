from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmployeeProfileRead(BaseModel):
    employee_id: str
    profile_bucket: Optional[str] = None
    profile_path: Optional[str] = None
    profile_mime: Optional[str] = None
    profile_size: Optional[int] = None
    profile_updated_at: Optional[datetime] = None

    # convenience for UI
    image_url: Optional[str] = None

    class Config:
        from_attributes = True
