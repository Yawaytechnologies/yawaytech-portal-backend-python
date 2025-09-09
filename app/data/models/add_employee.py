# app/data/models/add_employee.py  (adjust path/name as needed)
from __future__ import annotations
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    String,
    Date,
    DateTime,
    Text,
    Enum as SAEnum,
    UniqueConstraint,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.data.db import Base


class MaritalStatus(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"


class Department(str, Enum):
    HR = "HR"
    ENGINEERING = "Engineering"
    SALES = "Sales"
    MARKETING = "Marketing"
    FINANCE = "Finance"
    OPERATIONS = "Operations"
    IT = "IT"
    OTHER = "Other"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    father_name: Mapped[str] = mapped_column(String(120), nullable=False)

    employee_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    date_of_joining: Mapped[date] = mapped_column(Date, nullable=False)
    date_of_leaving: Mapped[date | None] = mapped_column(Date, nullable=True)

    email: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    mobile_number: Mapped[str] = mapped_column(String(20), nullable=False)

    marital_status: Mapped[MaritalStatus] = mapped_column(SAEnum(MaritalStatus), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    permanent_address: Mapped[str] = mapped_column(Text, nullable=False)

    designation: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[Department] = mapped_column(SAEnum(Department), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_employee_employee_id"),
        UniqueConstraint("email", name="uq_employee_email"),
    )
