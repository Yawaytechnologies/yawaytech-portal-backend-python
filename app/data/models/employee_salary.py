# app/data/models/employee_salary.py
from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.data.db import Base


class EmployeeSalary(Base):
    __tablename__ = "employee_salaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    base_salary: Mapped[float] = mapped_column(Float, nullable=False)
    gross_salary: Mapped[float] = mapped_column(Float, nullable=False)

    payroll_policy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payroll_policies.id"), nullable=True
    )
    policy = relationship("PayrollPolicy", back_populates="employee_salaries")

    breakdowns = relationship(
        "SalaryBreakdown", back_populates="salary", cascade="all, delete-orphan"
    )

    # Relationship back to employee
    employee = relationship("Employee", back_populates="salaries")
