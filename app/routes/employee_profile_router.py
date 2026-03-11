from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import logging

from app.data.db import get_db
from app.controllers.employee_profile_controller import EmployeeProfileController
from app.schemas.employee_profile import EmployeeProfileRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/employee-profiles", tags=["Employee Profiles"])
ctrl = EmployeeProfileController()


@router.get("/{employee_id}", response_model=EmployeeProfileRead)
def read_profile(employee_id: str, db: Session = Depends(get_db)):
    row, url = ctrl.get_profile(db, employee_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    out = EmployeeProfileRead.model_validate(row)
    out.image_url = url
    return out


@router.post("/{employee_id}/profile-image", response_model=EmployeeProfileRead)
async def upload_profile_image(
    employee_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        row, url = await ctrl.upload_profile_image(db, employee_id, file)
        out = EmployeeProfileRead.model_validate(row)
        out.image_url = url
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Profile image upload failed for employee {employee_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
