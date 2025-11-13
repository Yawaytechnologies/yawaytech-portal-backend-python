from __future__ import annotations
from datetime import date, timedelta
from typing import Optional, List, Dict

from sqlalchemy.orm import Session

from app.data.repositories.leave_repository import LeaveRepository, EIGHT_HOURS
from app.data.models.leave import LeaveType, LeaveRequest

# If you want a default cap for permission hours without schema change:
PERMISSION_MONTHLY_CAP_HOURS = 3.0  # tweak as needed


class LeaveService:
    def __init__(self, repo: Optional[LeaveRepository] = None):
        self.repo = repo or LeaveRepository()

    # ---- Types ----
    def create_type(self, db: Session, payload: dict) -> LeaveType:
        # code uniqueness handled by DB constraint; let exceptions bubble or pre-check:
        if self.repo.get_type(db, payload["code"]):
            raise ValueError("Leave type code already exists")
        return self.repo.create_type(db, payload)

    def list_types(self, db: Session) -> List[LeaveType]:
        return self.repo.list_types(db)

    def update_type(self, db: Session, code: str, patch: dict) -> LeaveType:
        lt = self.repo.update_type(db, code, patch)
        if not lt:
            raise ValueError("Leave type not found")
        return lt

    # ---- Holidays ----
    def create_holiday(self, db: Session, payload: dict):
        return self.repo.create_holiday(db, payload)

    def list_holidays(self, db: Session, start: date, end: date, region: Optional[str]):
        return self.repo.list_holidays(db, start, end, region)

    def update_holiday(self, db: Session, holiday_id: int, patch: dict):
        h = self.repo.update_holiday(db, holiday_id, patch)
        if not h:
            raise ValueError("Holiday not found")
        return h

    def delete_holiday(self, db: Session, holiday_id: int):
        ok = self.repo.delete_holiday(db, holiday_id)
        if not ok:
            raise ValueError("Holiday not found")
        return {"ok": True}

    # ---- Balances ----
    def seed_balances(self, db: Session, employee_id: str, year: int, items: List[dict]):
        # items: [{leave_type_code, opening_hours}]
        for it in items:
            lt = self.repo.get_type(db, it["leave_type_code"])
            if not lt:
                raise ValueError(f"Leave type {it['leave_type_code']} not found")
            self.repo.seed_balance(db, employee_id, year, lt, float(it.get("opening_hours", 0)))
        return {"ok": True}

    def adjust_balance(
        self, db: Session, employee_id: str, year: int, code: str, delta_hours: float
    ):
        lt = self.repo.get_type(db, code)
        if not lt:
            raise ValueError("Leave type not found")
        bal = self.repo.get_balance(db, employee_id, lt.id, year)
        if not bal:
            bal = self.repo.seed_balance(db, employee_id, year, lt, 0.0)
        self.repo.adjust_balance(db, bal, delta_hours)
        return {"ok": True, "new_closing_hours": float(bal.closing or 0)}

    def run_monthly_accrual(
        self,
        db: Session,
        year: int,
        month: int,
        employee_ids: List[str],
        per_type_hours: Dict[str, float],
    ):
        for emp in employee_ids:
            for code, hrs in per_type_hours.items():
                lt = self.repo.get_type(db, code)
                if not lt:
                    raise ValueError(f"Leave type {code} not found")
                bal = self.repo.get_balance(db, emp, lt.id, year)
                if not bal:
                    bal = self.repo.seed_balance(db, emp, year, lt, 0.0)
                self.repo.accrue_balance(db, bal, float(hrs))
        return {"ok": True}

    def list_balances(self, db: Session, employee_id: str, year: int):
        return self.repo.list_balances(db, employee_id, year)

    # ---- Requests ----
    def create_request_admin(self, db: Session, payload: dict) -> LeaveRequest:
        # map code -> type id
        lt = self.repo.get_type(db, payload["leave_type_code"])
        if not lt:
            raise ValueError("Leave type not found")

        row = self.repo.create_request(
            db,
            {
                "employee_id": payload["employee_id"],
                "leave_type_id": lt.id,
                "start_datetime": payload["start_datetime"],
                "end_datetime": payload["end_datetime"],
                "requested_unit": payload["requested_unit"],
                "requested_hours": payload.get("requested_hours"),
                "status": "PENDING",
                "reason": payload.get("reason"),
            },
        )
        return row

    def list_requests(self, db: Session, status: Optional[str] = None):
        return self.repo.list_requests(db, status)

    # ---- Approval / Rejection ----
    def decide_request(
        self, db: Session, req_id: int, decision: str, approver_id: str, note: Optional[str] = None
    ):
        req = self.repo.get_request(db, req_id)
        if not req:
            raise ValueError("Request not found")
        if req.status != "PENDING":
            raise ValueError("Request already decided")

        lt = db.get(LeaveType, req.leave_type_id)
        if not lt:
            raise ValueError("Leave type missing")

        if decision == "REJECTED":
            self.repo.set_request_status(db, req, "REJECTED", approver_id, note)
            return {"ok": True, "status": "REJECTED"}

        # APPROVAL path
        is_paid = bool(lt.is_paid)
        # figure hours to consume
        if req.requested_unit == "DAY":
            hours_per_day = EIGHT_HOURS
        elif req.requested_unit == "HALF_DAY":
            hours_per_day = EIGHT_HOURS / 2.0
        else:
            hours_per_day = float(req.requested_hours or 0.0)

        # Monthly permission cap if this type allows permission hours and unit=HOUR
        if lt.allow_permission_hours and req.requested_unit == "HOUR":
            y = req.start_datetime.date().year
            m = req.start_datetime.date().month
            used = self.repo.month_permission_hours(db, req.employee_id, lt.code, y, m)
            if used + hours_per_day > PERMISSION_MONTHLY_CAP_HOURS:
                raise ValueError(
                    f"Permission hours cap exceeded for {y}-{m:02d}. Used={used}, trying={hours_per_day}, cap={PERMISSION_MONTHLY_CAP_HOURS}"
                )

        # charge days
        # split by calendar days in [start..end]
        cur = req.start_datetime.date()
        end = req.end_datetime.date()
        total_hours = 0.0
        while cur <= end:
            apply_hours = (
                hours_per_day
                if req.requested_unit in {"DAY", "HALF_DAY"}
                else (hours_per_day if cur == req.start_datetime.date() else 0.0)
            )
            if apply_hours > 0:
                self.repo.upsert_attendance_leave(db, req.employee_id, cur, apply_hours, is_paid)
                total_hours += apply_hours
            cur += timedelta(days=1)

        # update balances if paid
        if is_paid:
            bal = self.repo.get_balance(db, req.employee_id, lt.id, req.start_datetime.year)
            if not bal:
                bal = self.repo.seed_balance(db, req.employee_id, req.start_datetime.year, lt, 0.0)
            # Ensure enough balance, or allow negative to represent deficit (your policy)
            if float(bal.closing or 0) < total_hours:
                # choose one policy: block, or allow negative. Here: block.
                raise ValueError(
                    f"Insufficient balance: need {total_hours}h, have {float(bal.closing or 0)}h"
                )
            self.repo.use_balance(db, bal, total_hours)

        self.repo.set_request_status(db, req, "APPROVED", approver_id, note)
        return {"ok": True, "status": "APPROVED", "hours_applied": total_hours}

    # ---- Permission usage helper ----
    def month_permission_usage(
        self, db: Session, employee_id: str, code: str, year: int, month: int
    ) -> float:
        return self.repo.month_permission_hours(db, employee_id, code, year, month)
