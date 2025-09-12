from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.data.db import get_db  # your existing session dependency
from app.data.models.add_employee import Department
from app.schemas.dashboard import EmployeesPage, EmployeeOut
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/employees", response_model=EmployeesPage)
def list_employees(
    department: Optional[Department] = Query(None, description="Filter by department"),
    limit: int = Query(20, ge=1, le=100, description="Page size (1..100)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    svc = DashboardService()
    items, total = svc.get_employees(db, department, limit, offset)
    return {
        "items": [EmployeeOut.model_validate(i) for i in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
