from __future__ import annotations
from typing import Annotated, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    status,
    Body,
    Form,
    File,
    UploadFile,
)
from sqlalchemy.orm import Session
from datetime import date

from app.data.db import get_db
from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.controllers.add_employee_controller import AddEmployeeController
from app.data.models.add_employee import MaritalStatus, Department
from app.core.config import settings
from app.core.image_utils import validate_image_upload

router = APIRouter(prefix="/api", tags=["Add Employee"])


def get_controller() -> AddEmployeeController:
    return AddEmployeeController()


@router.post("/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,  # Body marker not strictly needed here
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    try:
        return ctrl.create(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[EmployeeRead])
def list_employees(
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    rows, _ = ctrl.list_many(db, q=q, skip=skip, limit=min(limit, 100))
    return rows


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: str = Path(..., min_length=1),
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    emp = ctrl.get_one(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.put("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    payload: Annotated[EmployeeUpdate, Body(...)],
    employee_id: str = Path(..., min_length=1),  # <--- was ge=1
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    try:
        emp = ctrl.update(db, employee_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: str = Path(..., min_length=1),
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    ok = ctrl.delete(db, employee_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Employee not found")
    return None


# Form data endpoints for file uploads
@router.post("/employee/form/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def create_employee_with_form(
    name: str = Form(..., min_length=2, max_length=30),
    father_name: str = Form(..., min_length=2, max_length=30),
    date_of_birth: str = Form(...),
    employee_id: str = Form(..., min_length=9, max_length=9),
    date_of_joining: str = Form(...),
    date_of_leaving: str = Form(None),
    email: str = Form(...),
    mobile_number: str = Form(..., min_length=10, max_length=10, pattern=r"^\d{10}$"),
    pan_number: str = Form(..., min_length=10, max_length=10),
    aadhar_number: str = Form(..., min_length=12, max_length=12),
    marital_status: str = Form(...),
    permanent_address: str = Form(..., min_length=5),
    designation: str = Form(..., min_length=2, max_length=30),
    department: str = Form(...),
    password: str = Form(..., min_length=8),
    profile_picture: UploadFile = File(None),
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    """
    Create employee with form data including image upload.
    Supports multipart/form-data with file upload for profile picture.
    """
    try:
        # Validate required fields
        if not name or not father_name or not employee_id:
            raise HTTPException(
                status_code=400,
                detail="Name, father name, and employee ID are required",
            )

        # Convert date strings to date objects
        try:
            # Validate and convert date fields
            if not date_of_birth or date_of_birth == "string":
                raise HTTPException(status_code=400, detail="Date of birth is required")
            if not date_of_joining or date_of_joining == "string":
                raise HTTPException(status_code=400, detail="Date of joining is required")

            date_of_birth_obj = date.fromisoformat(date_of_birth)
            date_of_joining_obj = date.fromisoformat(date_of_joining)
            date_of_leaving_obj = (
                date.fromisoformat(date_of_leaving)
                if date_of_leaving and date_of_leaving != "string"
                else None
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format. Expected YYYY-MM-DD format, got: {date_of_birth}, {date_of_joining}, {date_of_leaving}",
            )

        # Validate profile picture if provided, but do not store image bytes
        # inline in the employee row. Inline base64 makes every employee list
        # response resend the full image payload.
        if profile_picture and profile_picture.filename:
            try:
                file_content = await profile_picture.read()
                validate_image_upload(
                    file_content,
                    profile_picture.content_type or "",
                    max_bytes=settings.PROFILE_IMAGE_MAX_BYTES,
                )

            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing profile picture: {str(e)}",
                )

        # Create EmployeeCreate object
        try:
            employee_data = EmployeeCreate(
                name=name,
                father_name=father_name,
                date_of_birth=date_of_birth_obj,
                employee_id=employee_id,
                date_of_joining=date_of_joining_obj,
                date_of_leaving=date_of_leaving_obj,
                email=email,
                mobile_number=mobile_number,
                pan_number=pan_number,
                aadhar_number=aadhar_number,
                marital_status=MaritalStatus(marital_status),
                permanent_address=permanent_address,
                designation=designation,
                department=Department(department),
                password=password,
                profile_picture=None,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid enum value or data error: {str(e)}",
            )

        return ctrl.create(db, employee_data)

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
