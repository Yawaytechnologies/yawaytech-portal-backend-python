from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import DB_URL  # adjust if your variable name is different

connect_args = {'check_same_thread': False} if DB_URL.startswith('sqlite') else {}

engine = create_engine(DB_URL, pool_pre_ping=True, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()






