from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.schemas.employee import EmployeeLogin, TokenOut
from app.services.employee_service import EmployeeService

router = APIRouter(prefix="/api/employee", tags=["employee"])
svc = EmployeeService()


@router.post("/login", response_model=TokenOut)
def login(payload: EmployeeLogin, db: Session = Depends(get_db)):
    token = svc.authenticate(db, payload.employee_id, payload.password)
    return {"access_token": token, "token_type": "bearer"}
