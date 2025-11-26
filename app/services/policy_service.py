# app/services/policy_service.py
from __future__ import annotations
from datetime import date
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.repositories.policy_repository import PolicyRepository
from app.schemas.policy_schma import (
    WorkweekUpsertRequest,
    WorkweekPolicyOut,
    HolidayCreateRequest,
    HolidayOut,
)


class PolicyService:
    def __init__(self, repo: Optional[PolicyRepository] = None):
        self.repo = repo or PolicyRepository()

    # ── Workweek ───────────────────────────────────────────────────────────────
    def list_workweeks(self, db: Session) -> List[WorkweekPolicyOut]:
        rows = self.repo.get_all_workweeks(db)
        return [
            WorkweekPolicyOut(id=row.id, region=row.region, policy_json=row.policy_json)
            for row in rows
        ]

    def create_workweek(self, db: Session, payload: WorkweekUpsertRequest) -> WorkweekPolicyOut:
        row = self.repo.create_workweek(db, payload.region, payload.policy)
        return WorkweekPolicyOut(id=row.id, region=row.region, policy_json=row.policy_json)

    # ── Holidays ───────────────────────────────────────────────────────────────
    def create_holiday(self, db: Session, payload: HolidayCreateRequest) -> HolidayOut:
        # (optional) prevent exact duplicates for same date/region/name
        existing = [
            h
            for h in self.repo.list_holidays(
                db, payload.holiday_date, payload.holiday_date, payload.region
            )
            if h.name.strip().lower() == payload.name.strip().lower()
        ]
        if existing:
            raise HTTPException(
                status_code=409, detail="Holiday already exists for that date/region/name."
            )

        h = self.repo.create_holiday(
            db=db,
            holiday_date=payload.holiday_date,
            name=payload.name.strip(),
            is_paid=payload.is_paid,
            region=payload.region,
            recurs_annually=payload.recurs_annually,
        )
        return HolidayOut(
            id=h.id,
            holiday_date=h.holiday_date,
            name=h.name,
            is_paid=h.is_paid,
            region=h.region,
            recurs_annually=h.recurs_annually,
        )

    def list_holidays(
        self, db: Session, date_from: date, date_to: date, region: Optional[str]
    ) -> List[HolidayOut]:
        if date_from > date_to:
            raise HTTPException(status_code=400, detail="date_from > date_to")
        rows = self.repo.list_holidays(db, date_from, date_to, region)
        return [
            HolidayOut(
                id=r.id,
                holiday_date=r.holiday_date,
                name=r.name,
                is_paid=r.is_paid,
                region=r.region,
                recurs_annually=r.recurs_annually,
            )
            for r in rows
        ]

    def delete_holiday(self, db: Session, holiday_id: int) -> None:
        h = self.repo.get_holiday(db, holiday_id)
        if not h:
            raise HTTPException(status_code=404, detail="Holiday not found")

        # Guard: do not allow delete if date inside a locked pay period
        if self.repo.is_period_locked_for_date(db, h.holiday_date):
            raise HTTPException(
                status_code=409,
                detail="Holiday falls within a locked pay period; unlock or create an adjusting entry instead.",
            )

        self.repo.delete_holiday(db, h)
