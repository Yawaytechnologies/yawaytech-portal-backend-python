from fastapi import FastAPI
from app.core.config import APP_NAME
from app.data.models import Base
from app.data.db import engine

# Dev convenience: auto-create tables (migrations recommended later)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=APP_NAME)

@app.get('/health')
def health():
    return {'status': 'ok'}
