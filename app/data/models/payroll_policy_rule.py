from sqlalchemy import Integer, String, Boolean, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.data.db import Base
from enum import Enum


class Ruletypes(str, Enum):
    ALLOWANCE = "ALLOWANCE"
    DEDUCTION = "DEDUCTION"


class PayrollPolicyRule(Base):
    __tablename__ = "payroll_policy_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_type: Mapped[Ruletypes] = mapped_column(
        SAEnum(Ruletypes, name="rule_type_enum"), nullable=False
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_percentage: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    applies_to: Mapped[str] = mapped_column(String(50), nullable=False)

    payroll_policy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payroll_policies.id"), nullable=False
    )

    policy = relationship("PayrollPolicy", back_populates="rules")
