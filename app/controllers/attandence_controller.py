from __future__ import annotations
from sqlalchemy.orm import Session
from datetime import date
from fastapi import UploadFile, HTTPException
from app.services.attendance_service import AttendanceService
from app.services.face_verification_service import FaceVerificationService
from app.schemas.attendance import (
    CheckInResponse,
    CheckOutResponse,
    TodayStatus,
    MonthDay,
    EmployeeAttendanceResponse,
    EmployeeMonthlyAttendanceResponse,
    EmployeeCheckInMonitoringResponse,
    CheckInWithFaceResponse,
    CheckOutWithFaceResponse,
    FaceVerificationResult,
    AttendanceEvidenceResponse,
)
from app.data.models.attendance_evidence import EvidenceType


class AttendanceController:
    def __init__(
        self,
        service: AttendanceService | None = None,
        face_service: FaceVerificationService | None = None,
    ):
        self.service = service or AttendanceService()
        self.face_service = face_service or FaceVerificationService()

    def check_in(self, db: Session, employee_id: str) -> CheckInResponse:
        s = self.service.check_in(db, employee_id)
        return CheckInResponse(
            sessionId=s.id,
            employeeId=s.employee_id,
            checkInUtc=s.check_in_utc,
            workDateLocal=s.work_date_local,
        )

    def check_out(self, db: Session, employee_id: str) -> CheckOutResponse:
        s = self.service.check_out(db, employee_id)
        worked = int((s.check_out_utc - s.check_in_utc).total_seconds()) if s.check_out_utc else 0
        return CheckOutResponse(
            sessionId=s.id,
            employeeId=s.employee_id,
            checkInUtc=s.check_in_utc,
            checkOutUtc=s.check_out_utc,
            workedSeconds=worked,
        )

    def today_status(self, db: Session, employee_id: str) -> TodayStatus:
        return TodayStatus(**self.service.today_status(db, employee_id))

    def month_view(self, db: Session, employee_id: str, year: int, month: int) -> list[MonthDay]:
        return [MonthDay(**d) for d in self.service.month_view(db, employee_id, year, month)]

    def get_employee_attendance(
        self,
        db: Session,
        employee_id: str,
        date_from: date,
        date_to: date,
        include_absent: bool,
    ) -> EmployeeAttendanceResponse:
        return self.service.get_employee_attendance(
            db=db,
            employee_id=employee_id,
            date_from=date_from,
            date_to=date_to,
            include_absent=include_absent,
        )

    def get_employee_month_report(
        self,
        db: Session,
        employee_id: str,
        year: int,
        month: int,
        include_absent: bool,
        working_days_only: bool,
        cap_to_today: bool,
    ) -> EmployeeMonthlyAttendanceResponse:
        return self.service.get_employee_month_report(
            db=db,
            employee_id=employee_id,
            year=year,
            month=month,
            include_absent=include_absent,
            working_days_only=working_days_only,
            cap_to_today=cap_to_today,
        )

    def get_employee_checkin_monitoring(
        self, db: Session, employee_id: str
    ) -> EmployeeCheckInMonitoringResponse:
        return self.service.get_employee_checkin_monitoring(db, employee_id)

    # ──────────────────────────────────────────────────────────────────────────────
    # Face Verification Methods
    # ──────────────────────────────────────────────────────────────────────────────

    async def check_in_with_face(
        self, db: Session, employee_id: str, selfie_file: UploadFile
    ) -> CheckInWithFaceResponse:
        """
        Check-in with face verification.
        CRITICAL: Face must be verified FIRST, only then attendance is recorded.

        Flow:
        1. Read selfie image
        2. Verify face FIRST (before any attendance record)
        3. If verified: Create attendance session
        4. Save evidence (for both success and failure - audit trail)
        5. Return appropriate response
        """
        # 1) Read selfie image first
        selfie_data = await selfie_file.read()
        selfie_mime = selfie_file.content_type or "image/jpeg"

        # 2) Verify face FIRST - before creating any attendance record
        verification_result = self.face_service.verify_face(
            db=db,
            employee_id=employee_id,
            selfie_image_data=selfie_data,
            selfie_mime=selfie_mime,
        )

        # Convert verification result to schema
        face_result = FaceVerificationResult(
            verified=verification_result["verified"],
            confidence_score=verification_result["confidence_score"],
            distance=verification_result.get("distance"),
            message=verification_result["message"],
            error=verification_result.get("error"),
        )

        # 3) ONLY create attendance if face is verified
        session = None
        if face_result.verified:
            # Face verified - create attendance session
            session = self.service.check_in(db, employee_id)
        else:
            # Face NOT verified - raise exception to prevent check-in
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Face verification failed. Check-in not recorded.",
                    "verified": False,
                    "confidence_score": face_result.confidence_score,
                    "debug_note": verification_result.get("debug_note", "Face not recognized"),
                },
            )

        # 4) Save evidence for audit trail
        evidence = self.face_service.save_evidence(
            db=db,
            session_id=session.id,
            evidence_type=EvidenceType.CHECK_IN,
            verified=face_result.verified,
            confidence_score=face_result.confidence_score,
            verification_notes=face_result.message,
        )

        db.commit()
        db.refresh(evidence)

        # Handle evidence_type - could be enum or string depending on source
        evidence_type_value = (
            evidence.evidence_type.value
            if hasattr(evidence.evidence_type, "value")
            else evidence.evidence_type
        )

        evidence_response = AttendanceEvidenceResponse(
            id=evidence.id,
            session_id=evidence.session_id,
            evidence_type=evidence_type_value,
            verified=evidence.verified,
            confidence_score=evidence.confidence_score,
            verification_notes=evidence.verification_notes,
            image_path=evidence.image_path,
            verified_at=evidence.verified_at,
            created_at=evidence.created_at,
        )

        return CheckInWithFaceResponse(
            sessionId=session.id,
            employeeId=session.employee_id,
            checkInUtc=session.check_in_utc,
            workDateLocal=session.work_date_local,
            faceVerification=face_result,
            evidence=evidence_response,
        )

    async def check_out_with_face(
        self, db: Session, employee_id: str, selfie_file: UploadFile
    ) -> CheckOutWithFaceResponse:
        """
        Check-out with face verification.
        CRITICAL: Face must be verified FIRST, only then attendance check-out is recorded.

        Flow:
        1. Read selfie image
        2. Verify face FIRST (before any check-out)
        3. If verified: Perform check-out (close session)
        4. Save evidence (for audit trail)
        5. Return appropriate response
        """
        # 1) Read selfie image first
        selfie_data = await selfie_file.read()
        selfie_mime = selfie_file.content_type or "image/jpeg"

        # 2) Verify face FIRST - before performing any check-out
        verification_result = self.face_service.verify_face(
            db=db,
            employee_id=employee_id,
            selfie_image_data=selfie_data,
            selfie_mime=selfie_mime,
        )

        # Convert verification result to schema
        face_result = FaceVerificationResult(
            verified=verification_result["verified"],
            confidence_score=verification_result["confidence_score"],
            distance=verification_result.get("distance"),
            message=verification_result["message"],
            error=verification_result.get("error"),
        )

        # 3) ONLY perform check-out if face is verified
        session = None
        if face_result.verified:
            # Face verified - perform check-out (close session)
            session = self.service.check_out(db, employee_id)
        else:
            # Face NOT verified - raise exception to prevent check-out
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Face verification failed. Check-out not recorded.",
                    "verified": False,
                    "confidence_score": face_result.confidence_score,
                    "debug_note": verification_result.get("debug_note", "Face not recognized"),
                },
            )

        worked = (
            int((session.check_out_utc - session.check_in_utc).total_seconds())
            if session.check_out_utc
            else 0
        )

        # 4) Save evidence for audit trail
        evidence = self.face_service.save_evidence(
            db=db,
            session_id=session.id,
            evidence_type=EvidenceType.CHECK_OUT,
            verified=face_result.verified,
            confidence_score=face_result.confidence_score,
            verification_notes=face_result.message,
        )

        db.commit()
        db.refresh(evidence)

        # Handle evidence_type - could be enum or string depending on source
        evidence_type_value = (
            evidence.evidence_type.value
            if hasattr(evidence.evidence_type, "value")
            else evidence.evidence_type
        )

        evidence_response = AttendanceEvidenceResponse(
            id=evidence.id,
            session_id=evidence.session_id,
            evidence_type=evidence_type_value,
            verified=evidence.verified,
            confidence_score=evidence.confidence_score,
            verification_notes=evidence.verification_notes,
            image_path=evidence.image_path,
            verified_at=evidence.verified_at,
            created_at=evidence.created_at,
        )

        return CheckOutWithFaceResponse(
            sessionId=session.id,
            employeeId=session.employee_id,
            checkInUtc=session.check_in_utc,
            checkOutUtc=session.check_out_utc,
            workedSeconds=worked,
            faceVerification=face_result,
            evidence=evidence_response,
        )

    # ──────────────────────────────────────────────────────────────────────────────
    # Evidence Query Methods
    # ──────────────────────────────────────────────────────────────────────────────

    def get_session_evidence(self, db: Session, session_id: int) -> list:
        """
        Get all evidence records for a specific attendance session.
        """
        from app.data.models.attendance_evidence import AttendanceEvidence
        from sqlalchemy import select

        stmt = select(AttendanceEvidence).where(AttendanceEvidence.session_id == session_id)
        evidences = list(db.execute(stmt).scalars().all())

        result = []
        for evidence in evidences:
            # Handle evidence_type - could be enum or string depending on source
            evidence_type_value = (
                evidence.evidence_type.value
                if hasattr(evidence.evidence_type, "value")
                else evidence.evidence_type
            )
            result.append(
                AttendanceEvidenceResponse(
                    id=evidence.id,
                    session_id=evidence.session_id,
                    evidence_type=evidence_type_value,
                    verified=evidence.verified,
                    confidence_score=evidence.confidence_score,
                    verification_notes=evidence.verification_notes,
                    image_path=evidence.image_path,
                    verified_at=evidence.verified_at,
                    created_at=evidence.created_at,
                )
            )
        return result

    def get_employee_evidence(
        self, db: Session, employee_id: str, date_from=None, date_to=None
    ) -> list:
        """
        Get all evidence records for an employee, optionally filtered by date range.
        """
        from app.data.models.attendance_evidence import AttendanceEvidence
        from app.data.models.attendance import AttendanceSession
        from sqlalchemy import select

        query = (
            select(AttendanceEvidence)
            .join(AttendanceSession)
            .where(AttendanceSession.employee_id == employee_id)
        )

        # Add date filters if provided
        if date_from:
            query = query.where(AttendanceSession.work_date_local >= date_from)
        if date_to:
            query = query.where(AttendanceSession.work_date_local <= date_to)

        query = query.order_by(AttendanceEvidence.created_at.desc())
        evidences = list(db.execute(query).scalars().all())

        result = []
        for evidence in evidences:
            # Handle evidence_type - could be enum or string depending on source
            evidence_type_value = (
                evidence.evidence_type.value
                if hasattr(evidence.evidence_type, "value")
                else evidence.evidence_type
            )
            result.append(
                AttendanceEvidenceResponse(
                    id=evidence.id,
                    session_id=evidence.session_id,
                    evidence_type=evidence_type_value,
                    verified=evidence.verified,
                    confidence_score=evidence.confidence_score,
                    verification_notes=evidence.verification_notes,
                    image_path=evidence.image_path,
                    verified_at=evidence.verified_at,
                    created_at=evidence.created_at,
                )
            )
        return result
