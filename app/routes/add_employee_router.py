# app/routes/add_employee_router.py
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
import base64

from app.data.db import get_db
from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.controllers.add_employee_controller import AddEmployeeController
from app.data.models.add_employee import MaritalStatus, Department

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
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    rows, _ = ctrl.list_many(db)
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


# @router.get("/", response_model=dict)
# def list_employees(
#     q: Optional[str] = Query(None, description="Search by employee_id"),
#     skip: int = Query(0, ge=0),
#     limit: int = Query(20, ge=1, le=100),
#     db: Session = Depends(get_db),
#     ctrl: AddEmployeeController = Depends(get_controller),
# ):
#     rows, total = ctrl.list_many(db, q=q, skip=skip, limit=limit)
#     return {"items": rows, "total": total, "skip": skip, "limit": limit}


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
@router.post("/form/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
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

        # Process profile picture if provided
        profile_picture_base64 = None
        if profile_picture and profile_picture.filename:
            try:
                # Validate file size (max 5MB)
                file_content = await profile_picture.read()
                if len(file_content) > 5 * 1024 * 1024:  # 5MB limit
                    raise HTTPException(
                        status_code=400,
                        detail="File size too large. Maximum 5MB allowed.",
                    )

                # Validate file type
                allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif"]
                if profile_picture.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
                    )

                # Convert to base64
                profile_picture_base64 = f"data:{profile_picture.content_type};base64,{base64.b64encode(file_content).decode()}"

            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing profile picture: {str(e)}",
                )

        # Create EmployeeCreate object
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
            profile_picture=profile_picture_base64,
        )

        return ctrl.create(db, employee_data)

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/form/{employee_id}", response_model=EmployeeRead)
async def update_employee_with_form(
    name: str = Form(None, min_length=2, max_length=30),
    father_name: str = Form(None, min_length=2, max_length=30),
    date_of_joining: str = Form(None),
    date_of_leaving: str = Form(None),
    email: str = Form(None),
    mobile_number: str = Form(None, min_length=10, max_length=10, pattern=r"^\d{10}$"),
    pan_number: str = Form(None, min_length=10, max_length=10),
    aadhar_number: str = Form(None, min_length=12, max_length=12),
    marital_status: str = Form(None),
    date_of_birth: str = Form(None),
    password: str = Form(None, min_length=8),
    permanent_address: str = Form(None, min_length=5),
    designation: str = Form(None, min_length=2, max_length=30),
    department: str = Form(None),
    profile_picture: UploadFile = File(None),
    employee_id: str = Path(..., min_length=1),
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    """
    Update employee with form data including image upload.
    Supports multipart/form-data with file upload for profile picture.
    """
    try:
        # Convert date strings to date objects
        try:
            # Validate and convert date fields for update
            date_of_birth_obj = (
                date.fromisoformat(date_of_birth)
                if date_of_birth and date_of_birth != "string"
                else None
            )
            date_of_joining_obj = (
                date.fromisoformat(date_of_joining)
                if date_of_joining and date_of_joining != "string"
                else None
            )
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

        # Process profile picture if provided
        profile_picture_base64 = None
        if profile_picture and profile_picture.filename:
            try:
                # Validate file size (max 5MB)
                file_content = await profile_picture.read()
                if len(file_content) > 5 * 1024 * 1024:  # 5MB limit
                    raise HTTPException(
                        status_code=400,
                        detail="File size too large. Maximum 5MB allowed.",
                    )

                # Validate file type
                allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif"]
                if profile_picture.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
                    )

                # Convert to base64
                profile_picture_base64 = f"data:{profile_picture.content_type};base64,{base64.b64encode(file_content).decode()}"

            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing profile picture: {str(e)}",
                )

        # Create EmployeeUpdate object
        update_data = EmployeeUpdate(
            name=name,
            father_name=father_name,
            employee_id=employee_id,
            date_of_joining=date_of_joining_obj,
            date_of_leaving=date_of_leaving_obj,
            email=email,
            mobile_number=mobile_number,
            pan_number=pan_number,
            aadhar_number=aadhar_number,
            marital_status=MaritalStatus(marital_status) if marital_status else None,
            date_of_birth=date_of_birth_obj,
            password=password,
            permanent_address=permanent_address,
            designation=designation,
            department=Department(department) if department else None,
            profile_picture=profile_picture_base64,
        )

        emp = ctrl.update(db, employee_id, update_data)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return emp

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
