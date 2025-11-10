from app.data.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT unnest(enum_range(NULL::expense_category)) as values")
    )
    print([row[0] for row in result])
