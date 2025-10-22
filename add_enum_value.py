from app.data.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TYPE expense_category ADD VALUE IF NOT EXISTS 'Shopping'"))
    conn.commit()
    print("Added Shopping to enum")
