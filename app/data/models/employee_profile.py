from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.data.db import Base


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id = Column(Integer, primary_key=True)
    employee_id = Column(
        String(32),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    employee_code = Column(String(32), nullable=True)

    profile_bucket = Column(String(128), nullable=True)
    profile_path = Column(String, nullable=True)
    profile_mime = Column(String(64), nullable=True)
    profile_size = Column(Integer, nullable=True)

    profile_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
