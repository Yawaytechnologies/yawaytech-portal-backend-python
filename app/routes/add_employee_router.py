# app/routes/add_employee_router.py
from typing import List, Tuple, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.data.db import get_db
from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.services.add_employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["Employees"])
svc = EmployeeService()

@router.post("/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_employee(db, payload)
    except ValueError as e:
        # e.g., duplicate employee_id/email
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{id_}", response_model=EmployeeRead)
def get_employee(id_: int = Path(..., ge=1), db: Session = Depends(get_db)):
    try:
        return svc.get_employee(db, id_)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=List[EmployeeRead])
def list_employees(
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    designation: Optional[str] = Query(None),
    marital_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    items, total = svc.list_employees(
        db, q=q, page=page, size=size, designation=designation, marital_status=marital_status
    )
    # Optionally expose total via header
    # from fastapi import Response
    # response.headers["X-Total-Count"] = str(total)
    return items

@router.put("/{id_}", response_model=EmployeeRead)
@router.patch("/{id_}", response_model=EmployeeRead)
def update_employee(id_: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    try:
        return svc.update_employee(db, id_, payload)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(id_: int, db: Session = Depends(get_db)):
    try:
        svc.delete_employee(db, id_)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None
