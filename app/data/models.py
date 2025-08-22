from sqlalchemy.orm import declarative_base
Base = declarative_base()
# You'll add Category and Expense models here later.


from sqlalchemy import Column, Integer, String, Float, Date
from app.data.db import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(250), nullable=True)
    added_by = Column(String(100), nullable=False)
