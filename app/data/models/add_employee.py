# app/models/add_employee_model.py
from __future__ import annotations
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Text,
    Enum as SAEnum,
    UniqueConstraint,
)
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

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(120), nullable=False)
    father_name = Column(String(120), nullable=False)

    employee_id = Column(String(50), nullable=False, unique=True, index=True)

    date_of_joining = Column(Date, nullable=False)
    date_of_leaving = Column(Date, nullable=True)

    email = Column(String(160), nullable=False, unique=True, index=True)
    mobile_number = Column(String(20), nullable=False)

    marital_status = Column(SAEnum(MaritalStatus), nullable=False)
    date_of_birth = Column(Date, nullable=False)

    permanent_address = Column(Text, nullable=False)

    designation = Column(String(120), nullable=False)
    department = Column(SAEnum(Department), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_employee_employee_id"),
        UniqueConstraint("email", name="uq_employee_email"),
    )
