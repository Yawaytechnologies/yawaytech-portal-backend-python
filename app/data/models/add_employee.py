# app/data/models/add_employee.py
from __future__ import annotations
from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SAEnum, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.data.db import Base


class MaritalStatus(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"


class Department(str, Enum):
    HR = "HR"
    IT = "IT"
    SALES = "Sales"
    FINANCE = "Finance"
    MARKETING = "Marketing"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(30), nullable=False)
    father_name: Mapped[str] = mapped_column(String(30), nullable=False)

    employee_id: Mapped[str] = mapped_column(String(9), nullable=False, unique=True, index=True)

    date_of_joining: Mapped[date] = mapped_column(Date, nullable=False)
    date_of_leaving: Mapped[date | None] = mapped_column(Date, nullable=True)

    email: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    mobile_number: Mapped[str] = mapped_column(String(10), nullable=False)

    marital_status: Mapped[MaritalStatus] = mapped_column(SAEnum(MaritalStatus), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    permanent_address: Mapped[str] = mapped_column(Text, nullable=False)

    designation: Mapped[str] = mapped_column(String(30), nullable=False)
    department: Mapped[Department] = mapped_column(SAEnum(Department), nullable=False, index=True)
    profile_picture: Mapped[str | None] = mapped_column(Text, nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_employee_employee_id"),
        UniqueConstraint("email", name="uq_employee_email"),
        UniqueConstraint("mobile_number", name="uq_employee_mobile_number"),
    )

    # Index("ix_employees_dept_name", Employee.department, Employee.name)
    # Index("ix_employees_employee_id", Employee.employee_id, unique=True)
