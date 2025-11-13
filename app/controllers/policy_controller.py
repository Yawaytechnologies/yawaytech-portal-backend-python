# app/controllers/admin_policy_controller.py
from __future__ import annotations
from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session

from app.schemas.policy_schma import (
    WorkweekUpsertRequest,
    WorkweekPolicyOut,
    HolidayCreateRequest,
    HolidayOut,
)
from app.services.policy_service import PolicyService


class AdminPolicyController:
    def __init__(self, service: Optional[PolicyService] = None):
        self.service = service or PolicyService()

    # Workweek
    def upsert_workweek(self, db: Session, payload: WorkweekUpsertRequest) -> WorkweekPolicyOut:
        return self.service.upsert_workweek(db, payload)

    # Holidays
    def create_holiday(self, db: Session, payload: HolidayCreateRequest) -> HolidayOut:
        return self.service.create_holiday(db, payload)

    def list_holidays(
        self, db: Session, date_from: date, date_to: date, region: Optional[str]
    ) -> List[HolidayOut]:
        return self.service.list_holidays(db, date_from, date_to, region)

    def delete_holiday(self, db: Session, holiday_id: int) -> dict:
        self.service.delete_holiday(db, holiday_id)
        return {"ok": True}
