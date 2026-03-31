"""
Attendance Evidence Model - stores face verification results for check-in/check-out.

The registration profile image remains in storage and is used for verification.
Check-in/check-out selfies are processed in-memory and are not persisted.
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

    Each check-in or check-out verifies a live selfie against the employee's
    stored profile image, but only the verification result is persisted.

    Fields explained:
    - session_id: Links to AttendanceSession (FK)
    - evidence_type: Whether this is check-in or check-out evidence
    - image_bucket: Optional storage bucket name if an image is retained
    - image_path: Optional storage path if an image is retained
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
    image_bucket: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_mime: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
