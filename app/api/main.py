from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import APP_NAME
from app.data.db import get_db

# Routers
from app.routes.expenses_router import router as expenses_router
from app.routes.add_employee_router import router as add_employee_router
from app.routes import admin_router, proctected_example_router, employee_router
from app.routes.attendance_router import router as attendance_router
from app.routes.worklog_router import router as worklog_router
from app.routes.leave_admin_router import router as leave_admin_router
from app.routes.policy_router import router as policy_router
from app.routes.leave_employee_router import router as leave_employee_router
from app.routes.shift_router import router as shift_router
from app.routes.monthly_summary_router import router as monthly_summary_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    print("🚀 App startup initiated")
    yield
    print("🛑 App shutdown triggered")


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
        "https://main.d5928n6qpn0dc.amplifyapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(employee_router.router)
app.include_router(admin_router.router)
app.include_router(proctected_example_router.router)
app.include_router(attendance_router)
app.include_router(expenses_router, prefix="")
app.include_router(employee_router.router, prefix="/api", tags=["employee"])
app.include_router(add_employee_router)  # Added to include add_employee_router routes

app.include_router(worklog_router, prefix="")
app.include_router(leave_admin_router, prefix="")
app.include_router(policy_router, prefix="")
app.include_router(leave_employee_router, prefix="")
app.include_router(shift_router, prefix="") 
app.include_router(monthly_summary_router, prefix="")

# Health check routes
@app.get("/")
def root():
    print("✅ Root route hit")
    return {"message": "Expense Manager API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"ok": True}


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
