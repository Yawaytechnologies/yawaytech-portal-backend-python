"""
Attendance Evidence Model - stores face verification evidence for check-in/check-out.

Flow:
1. User sends selfie for check-in/check-out
2. FaceVerificationService compares selfie against employee's profile image
3. If faces match (similarity >= 0.6), evidence is saved with verified=True
4. If no match, evidence is saved with verified=False (for audit trail)
5. Evidence images stored in Supabase storage with path like:
   attendance/{employee_id}/{work_date}/check_in_{timestamp}.jpg
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.data.db import Base


class EvidenceType(str, Enum):
    """Type of attendance evidence being captured."""

    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"


class AttendanceEvidence(Base):
    """
    Stores face verification evidence for attendance sessions.

    Each check-in or check-out can capture a selfie image and verify it
    against the employee's stored profile image.

    Fields explained:
    - session_id: Links to AttendanceSession (FK)
    - evidence_type: Whether this is check-in or check-out evidence
    - image_bucket: Supabase bucket name (e.g., "daily_attandance")
    - image_path: Path in bucket where selfie is stored
    - verified: True if face matched with confidence >= 0.6
    - confidence_score: Similarity score between profile and selfie (0.0-1.0)
      • 0.0 = no match (face not detected or no features found)
      • 0.6+ = match acceptable
      • 1.0 = perfect match (unlikely)
    - verification_notes: Reason for failure (e.g., "No face detected in selfie")
    """

    __tablename__ = "attendance_evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to attendance_sessions
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Type of evidence (check_in or check_out)
    # Use values_callable to ensure SQLAlchemy uses the enum's VALUE (e.g., "check_in")
    # rather than the enum's NAME (e.g., "CHECK_IN") when saving to PostgreSQL
    evidence_type: Mapped[EvidenceType] = mapped_column(
        SAEnum(EvidenceType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    # Storage details
    image_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    image_mime: Mapped[str] = mapped_column(String(64), nullable=True)
    image_size: Mapped[int] = mapped_column(Integer, nullable=True)

    # Verification results
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    verification_notes: Mapped[str] = mapped_column(String(512), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="NOW()",
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="NOW()",
        nullable=False,
    )

    __table_args__ = (
        Index("ix_evidence_session_type", "session_id", "evidence_type"),
        Index("ix_evidence_verified", "verified"),
    )
