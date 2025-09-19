# app/routes/add_employee_router.py
from __future__ import annotations
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Path, status, Body
from sqlalchemy.orm import Session

from app.data.db import get_db
from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.controllers.add_employee_controller import AddEmployeeController

router = APIRouter(prefix="/employees", tags=["Employees"])


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
