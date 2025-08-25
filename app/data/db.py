from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base,Session

DATABASE_URL = "postgresql://myuser:yaway%40123@localhost:5432/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ✅ This is what FastAPI will use to get a DB session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()