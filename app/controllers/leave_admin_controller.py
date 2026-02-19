# app/controllers/leave_admin_controller.py
from __future__ import annotations
from datetime import date, timedelta
from typing import Optional, List, Dict, Sequence, Mapping, Any

from sqlalchemy.orm import Session

from app.data.repositories.leave_repository import LeaveRepository, EIGHT_HOURS
from app.data.models.leave import LeaveType, LeaveRequest, LeaveStatus, LeaveReqUnit

# If you want a default cap for permission hours without schema change:
PERMISSION_MONTHLY_CAP_HOURS = 3.0  # tweak as needed


class LeaveAdminController:
    def __init__(self, repo: Optional[LeaveRepository] = None):
        self.repo = repo or LeaveRepository()

    # ---- Types ----
    def create_type(self, db: Session, payload: dict) -> dict:
        # code uniqueness handled by DB constraint; let exceptions bubble or pre-check:
        if self.repo.get_type(db, payload["code"]):
            raise ValueError("Leave type code already exists")
        lt = self.repo.create_type(db, payload)
        return {
            "id": lt.id,
            "code": lt.code,
            "name": lt.name,
            "unit": lt.unit.value if hasattr(lt.unit, "value") else str(lt.unit),
            "is_paid": lt.is_paid,
            "allow_half_day": lt.allow_half_day,
            "allow_permission_hours": lt.allow_permission_hours,
            "duration_days": lt.duration_days,
            "monthly_limit": lt.monthly_limit,
            "yearly_limit": lt.yearly_limit,
            "carry_forward_allowed": lt.carry_forward_allowed,
        }

    def list_types(self, db: Session) -> List[LeaveType]:
        return self.repo.list_types(db)

    def update_type(self, db: Session, code: str, patch: dict) -> dict:
        lt = self.repo.update_type(db, code, patch)
        if not lt:
            raise ValueError("Leave type not found")
        return {
            "id": lt.id,
            "code": lt.code,
            "name": lt.name,
            "unit": lt.unit.value if hasattr(lt.unit, "value") else str(lt.unit),
            "is_paid": lt.is_paid,
            "allow_half_day": lt.allow_half_day,
            "allow_permission_hours": lt.allow_permission_hours,
        }

    def delete_type(self, db: Session, code: str) -> dict:
        ok = self.repo.delete_type(db, code)
        if not ok:
            raise ValueError("Leave type not found")
        return {"ok": True}

    # ---- Holidays ----
    def create_holiday(self, db: Session, payload: dict):
        h = self.repo.create_holiday(db, payload)
        return {
            "id": h.id,
            "holiday_date": h.holiday_date.isoformat(),
            "name": h.name,
            "is_paid": h.is_paid,
            "region": h.region,
            "recurs_annually": h.recurs_annually,
        }

    def list_holidays(self, db: Session, start: date, end: date, region: Optional[str]):
        return self.repo.list_holidays(db, start, end, region)

    def update_holiday(self, db: Session, holiday_id: int, patch: dict):
        h = self.repo.update_holiday(db, holiday_id, patch)
        if not h:
            raise ValueError("Holiday not found")
        return {
            "id": h.id,
            "holiday_date": h.holiday_date.isoformat(),
            "name": h.name,
            "is_paid": h.is_paid,
            "region": h.region,
            "recurs_annually": h.recurs_annually,
        }

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
            self.repo.seed_balance(
                db,
                employee_id,
                year,
                lt,
                float(it.get("opening_hours", 0)),
            )
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

    # ---- Accrual ----
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

    # this is what the router calls: /accrual/run
    def run_accrual(
        self,
        db: Session,
        year: int,
        month: int,
        employee_ids: Sequence[str],
        per_type_hours: Mapping[str, float],
    ) -> dict[str, Any]:
        # just delegate to run_monthly_accrual for now
        return self.run_monthly_accrual(
            db,
            year,
            month,
            list(employee_ids),
            dict(per_type_hours),
        )

    def list_balances(self, db: Session, employee_id: str, year: int):
        return self.repo.list_balances(db, employee_id, year)

    # ---- Requests ----
    def create_request_admin(self, db: Session, payload: dict) -> LeaveRequest:
        # map code -> type id
        lt = self.repo.get_type(db, payload["leave_type_code"])
        if not lt:
            raise ValueError("Leave type not found")

        # Monthly leave type limit check (e.g., CL can be taken only once per month)
        year = payload["start_datetime"].year
        month = payload["start_datetime"].month
        if self.repo.has_approved_leave_in_month(
            db, payload["employee_id"], payload["leave_type_code"], year, month
        ):
            raise ValueError(
                f"Employee has already taken {payload['leave_type_code']} leave this month ({year}-{month:02d}). Only one {payload['leave_type_code']} leave per month is allowed."
            )

        row = self.repo.create_request(
            db,
            {
                "employee_id": payload["employee_id"],
                "leave_type_id": lt.id,
                "start_datetime": payload["start_datetime"],
                "end_datetime": payload["end_datetime"],
                "requested_unit": payload["requested_unit"],  # LeaveReqUnit via Pydantic
                "requested_hours": payload.get("requested_hours"),
                "status": LeaveStatus.PENDING,  # enum, not raw string
                "reason": payload.get("reason"),
            },
        )
        return row

    def list_requests(self, db: Session, status: Optional[LeaveStatus] = None) -> List[dict]:
        return self.repo.list_requests(db, status)

    # ---- Approval / Rejection ----
    def decide_request(
        self,
        db: Session,
        req_id: int,
        decision: str,
        approver_id: str,
        note: Optional[str] = None,
    ):
        req = self.repo.get_request(db, req_id)
        if not req:
            raise ValueError("Request not found")
        if req.status != LeaveStatus.PENDING:
            raise ValueError("Request already decided")

        lt = db.get(LeaveType, req.leave_type_id)
        if not lt:
            raise ValueError("Leave type missing")

        if decision == "REJECTED":
            self.repo.set_request_status(db, req, "REJECTED", approver_id, note)
            return {"ok": True, "status": "REJECTED"}

        # ───────────────── APPROVAL PATH ─────────────────
        is_paid_type = bool(lt.is_paid)

        # figure hours to consume per unit
        if req.requested_unit == LeaveReqUnit.DAY:
            hours_per_unit = EIGHT_HOURS
        elif req.requested_unit == LeaveReqUnit.HALF_DAY:
            hours_per_unit = EIGHT_HOURS / 2.0
        else:  # HOUR
            hours_per_unit = float(req.requested_hours or 0.0)

        # Monthly permission cap if this type allows permission hours and unit=HOUR
        if lt.allow_permission_hours and req.requested_unit == LeaveReqUnit.HOUR:
            y = req.start_datetime.date().year
            m = req.start_datetime.date().month
            used = self.repo.month_permission_hours(db, req.employee_id, lt.code, y, m)
            if used + hours_per_unit > PERMISSION_MONTHLY_CAP_HOURS:
                raise ValueError(
                    f"Permission hours cap exceeded for {y}-{m:02d}. "
                    f"Used={used}, trying={hours_per_unit}, cap={PERMISSION_MONTHLY_CAP_HOURS}"
                )

        # ── 1) Build per-day segments (NO DB writes yet) ──
        cur = req.start_datetime.date()
        end = req.end_datetime.date()
        total_hours = 0.0
        segments: list[tuple[date, float]] = []

        while cur <= end:
            if req.requested_unit in {LeaveReqUnit.DAY, LeaveReqUnit.HALF_DAY}:
                apply_hours = hours_per_unit
            else:
                # HOUR → only first day carries the hours
                apply_hours = hours_per_unit if cur == req.start_datetime.date() else 0.0

            if apply_hours > 0:
                segments.append((cur, apply_hours))
                total_hours += apply_hours

            cur += timedelta(days=1)

        # ── 2) Decide whether this approval is PAID or LOP ──
        # default: follow leave type (paid/unpaid)
        final_is_paid = is_paid_type

        if is_paid_type:
            bal = self.repo.get_balance(db, req.employee_id, lt.id, req.start_datetime.year)
            if not bal:
                bal = self.repo.seed_balance(db, req.employee_id, req.start_datetime.year, lt, 0.0)

            closing = float(bal.closing or 0.0)

            if closing < total_hours:
                # OLD: block
                #   raise ValueError(f"Insufficient balance: need {total_hours}h, have {closing}h")
                #
                # NEW: approve as LOP (unpaid), do NOT touch balance
                final_is_paid = False
            else:
                # enough balance → consume and keep as paid
                self.repo.use_balance(db, bal, total_hours)
                final_is_paid = True

        # ── 3) Now write attendance rows with the final is_paid flag ──
        for day, apply_hours in segments:
            self.repo.upsert_attendance_leave(
                db,
                req.employee_id,
                day,
                apply_hours,
                final_is_paid,
            )

        # ── 4) Mark request approved ──
        self.repo.set_request_status(db, req, "APPROVED", approver_id, note)
        return {"ok": True, "status": "APPROVED", "hours_applied": total_hours}

    # ---- Permission usage helper ----
    def month_permission_usage(
        self, db: Session, employee_id: str, code: str, year: int, month: int
    ) -> float:
        return self.repo.month_permission_hours(db, employee_id, code, year, month)
