# app/api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import APP_NAME

# NOTE: Do NOT import Base/engine just to run create_all on startup.
# from app.data.db import engine, Base  # ← removed

# Routers
from app.routes.expenses_router import router as expenses_router
from app.routes.add_employee_router import router as add_employee_router
from app.routes.dashboard_router import router as dashboard_router
from app.routes import admin_router, proctected_example_router, employee_router
from app.routes.attendance_router import router as attendance_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # ❌ No DDL on startup. Use Alembic or one-off script against 5432 for schema.
    # If you really want a non-fatal DB warmup ping, you can do it here—but NEVER raise.
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

# Mount routers
app.include_router(employee_router.router)
app.include_router(admin_router.router)
app.include_router(proctected_example_router.router)
app.include_router(expenses_router, prefix="")  # e.g. /expenses
app.include_router(add_employee_router, prefix="/api")  # -> /api/employees
app.include_router(attendance_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")  # e.g. /api/dashboard


# Health & Root
@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Expense Manager API is running"}


# ---- Minimal global error handlers ----
@app.exception_handler(Exception)
async def unhandled_exceptions(_: Request, __: Exception):
    # Log details internally in real apps; keep response generic
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
