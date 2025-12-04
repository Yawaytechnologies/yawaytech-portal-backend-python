# app/data/models/salary_breakdown.py
from sqlalchemy import Column, Integer, Float, ForeignKey, String, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.data.db import Base
from enum import Enum


class Ruletypes(str, Enum):
    ALLOWANCE = "ALLOWANCE"
    DEDUCTION = "DEDUCTION"


class SalaryBreakdown(Base):
    __tablename__ = "salary_breakdowns"

    id = Column(Integer, primary_key=True, index=True)
    employee_salary_id = Column(Integer, ForeignKey("employee_salaries.id"), nullable=False)

    rule_name = Column(String(100), nullable=False)
    rule_type: Mapped[Ruletypes] = mapped_column(
        SAEnum(Ruletypes, name="rule_type_enum"), nullable=False
    )
    applies_to = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)

    salary = relationship("EmployeeSalary", back_populates="breakdowns")
