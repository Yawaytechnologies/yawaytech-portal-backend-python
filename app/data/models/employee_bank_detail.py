from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.data.db import Base


class EmployeeBankDetail(Base):
    __tablename__ = "employee_bank_details"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=False)
    ifsc_code = Column(String(20), nullable=False)
    branch_name = Column(String(100), nullable=True)

    # Relationship back to employee
    employee = relationship("Employee", back_populates="bank_details")
