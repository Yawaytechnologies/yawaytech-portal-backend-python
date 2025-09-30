from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import APP_NAME
from app.data.db import engine, get_db

# Import all models to register them before create_all (for dev only)

# Routers
from app.routes.expenses_router import router as expenses_router
from app.routes.add_employee_router import router as add_employee_router
from app.routes.dashboard_router import router as dashboard_router
from app.routes import admin_router, proctected_example_router, employee_router
from app.routes.attendance_router import router as attendance_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        with engine.connect() as conn:
            try:
                who = conn.execute(text("select current_user")).scalar()
            except Exception as e:
                who = f"error: {e}"

            try:
                ssl = conn.execute(text("show ssl")).scalar()
            except Exception:
                ssl = "N/A"

            print(f"[DB] current_user at startup: {who} | ssl={ssl}")
    except Exception as e:
        print(f"[DB] startup identity check failed: {e}")
    finally:
        yield  # ✅ Always yield, even if errors occurred


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
        "http://127.0.0.1:5174",
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
app.include_router(expenses_router, prefix="")
app.include_router(add_employee_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


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


# Debug DB connection
@app.get("/debug/db")
def debug_db(db: Session = Depends(get_db)):
    try:
        who = db.execute(text("select current_user")).scalar()
        return {"connected": True, "current_user": who}
    except Exception as e:
        return {"connected": False, "error": str(e)}


# Global error handlers
@app.exception_handler(Exception)
async def unhandled_exceptions(_: Request, __: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
