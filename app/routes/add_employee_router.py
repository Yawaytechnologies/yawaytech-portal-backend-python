# app/routes/add_employee_router.py
from __future__ import annotations
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
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


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: str = Path(..., ge=1),
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    emp = ctrl.get_one(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp



@router.get("/", response_model=dict)
def list_employees(
    q: Optional[str] = Query(None, description="Search by employee_id/department"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    rows, total = ctrl.list_many(db, q=q, skip=skip, limit=limit)
    return {"items": rows, "total": total, "skip": skip, "limit": limit}


@router.put("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    payload: Annotated[EmployeeUpdate, Body(...)],  # <-- no default here
    employee_id: str = Path(..., ge=1),  # defaults follow
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


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    id_: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    ctrl: AddEmployeeController = Depends(get_controller),
):
    ok = ctrl.delete(db, id_)
    if not ok:
        raise HTTPException(status_code=404, detail="Employee not found")
    return None
