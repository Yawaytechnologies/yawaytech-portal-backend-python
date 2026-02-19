from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.orm import relationship
from app.data.db import Base


class PayrollPolicy(Base):
    __tablename__ = "payroll_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    rules = relationship("PayrollPolicyRule", back_populates="policy", cascade="all, delete-orphan")
    employee_salaries = relationship("EmployeeSalary", back_populates="policy")
