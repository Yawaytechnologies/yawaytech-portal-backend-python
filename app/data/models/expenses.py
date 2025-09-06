from sqlalchemy import Column, Date, Float, Integer, String, Text

from app.data.db import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)  # Text is better for longer content
    added_by = Column(String(100), nullable=False)
