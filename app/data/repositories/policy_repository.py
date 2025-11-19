# app/data/repositories/policy_repository.py
from __future__ import annotations
from datetime import date
from typing import Optional, List, Dict

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.data.models.policy import WorkweekPolicy, HolidayCalendar
# from app.data.models.payroll import PayPeriod  # Commented out as payroll is removed


class PolicyRepository:
    # ── Workweek ───────────────────────────────────────────────────────────────
    def get_workweek_by_region(self, db: Session, region: str) -> Optional[WorkweekPolicy]:
        stmt = select(WorkweekPolicy).where(WorkweekPolicy.region == region)
        return db.execute(stmt).scalar_one_or_none()

    def upsert_workweek(self, db: Session, region: str, policy_json: Dict) -> WorkweekPolicy:
        row = self.get_workweek_by_region(db, region)
        if row:
            row.policy_json = policy_json
        else:
            row = WorkweekPolicy(region=region, policy_json=policy_json)
            db.add(row)
        db.flush()
        db.commit()
        return row

    # ── Holidays ───────────────────────────────────────────────────────────────
    def create_holiday(
        self,
        db: Session,
        holiday_date: date,
        name: str,
        is_paid: bool,
        region: Optional[str],
        recurs_annually: bool,
    ) -> HolidayCalendar:
        h = HolidayCalendar(
            holiday_date=holiday_date,
            name=name,
            is_paid=is_paid,
            region=region,
            recurs_annually=recurs_annually,
        )
        db.add(h)
        db.flush()
        db.commit()
        return h

    def list_holidays(
        self,
        db: Session,
        date_from: date,
        date_to: date,
        region: Optional[str] = None,
    ) -> List[HolidayCalendar]:
        stmt = select(HolidayCalendar).where(
            and_(
                HolidayCalendar.holiday_date >= date_from,
                HolidayCalendar.holiday_date <= date_to,
            )
        )
        if region is not None:
            stmt = stmt.where(
                (HolidayCalendar.region == region) | (HolidayCalendar.region.is_(None))
            )
        stmt = stmt.order_by(HolidayCalendar.holiday_date.asc())
        return list(db.execute(stmt).scalars().all())

    def get_holiday(self, db: Session, holiday_id: int) -> Optional[HolidayCalendar]:
        stmt = select(HolidayCalendar).where(HolidayCalendar.id == holiday_id)
        return db.execute(stmt).scalar_one_or_none()

    def delete_holiday(self, db: Session, holiday: HolidayCalendar) -> None:
        db.delete(holiday)
        db.flush()

    # ── Period locking guard for deletes ───────────────────────────────────────
    def is_period_locked_for_date(self, db: Session, d: date) -> bool:
        """
        Returns True if any PayPeriod covering date `d` is locked.
        Since payroll is removed, this always returns False.
        """
        # stmt = select(PayPeriod).where(
        #     and_(PayPeriod.start_date <= d, PayPeriod.end_date >= d, PayPeriod.is_locked.is_(True))
        # )
        # return db.execute(stmt).first() is not None
        return False
