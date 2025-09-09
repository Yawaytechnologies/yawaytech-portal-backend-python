# app/api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import APP_NAME
from app.data.db import engine, Base
from starlette.exceptions import HTTPException as StarletteHTTPException

# Routers
from app.routes.expenses_router import router as expenses_router
from app.routes.add_employee_router import router as add_employee_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables at startup (use Alembic in prod)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=APP_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
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

# Routers
app.include_router(expenses_router, prefix="")  # e.g. /expenses
app.include_router(add_employee_router, prefix="/api")  # -> /api/employees


# Health & Root
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Expense Manager API is running"}


# ---- Optional: minimal global error handlers ----
@app.exception_handler(Exception)
async def unhandled_exceptions(_: Request, exc: Exception):
    # Avoid leaking internals; log details in real apps.
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
