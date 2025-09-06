# app/api/main.py  (or app/main.py — just be consistent with your imports)
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME
from app.data.db import engine  # engine lives in db.py
from app.data.db import Base  # Base lives in db.py

# Routers (import the router objects explicitly)
from app.routes.expenses_router import router as expenses_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables at startup (use Alembic later in prod)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)

# CORS for your local frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://yawaytech-portal-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers once
app.include_router(expenses_router, prefix="")  # e.g. /expenses


# Simple health & root endpoints
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Expense Manager API is running"}
