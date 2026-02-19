# app/services/add_employee_service.py
from __future__ import annotations
from typing import List, Optional, Tuple, cast
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.security import hash_password
from app.data.models.add_employee import Employee, Department
from app.schemas.add_employee import EmployeeCreate, EmployeeUpdate, EmployeeRead


class EmployeeService:
    def create_employee(self, db: Session, payload: EmployeeCreate) -> Employee:
        exists_email = db.scalar(
            select(func.count()).select_from(Employee).where(Employee.email == payload.email)
        )
        if exists_email:
            raise ValueError("Email already exists")

        exists_empid = db.scalar(
            select(func.count())
            .select_from(Employee)
            .where(Employee.employee_id == payload.employee_id)
        )
        if exists_empid:
            raise ValueError("Employee ID already exists")

        # If you're on Pydantic v2, prefer payload.model_dump()
        data = payload.dict()
        data["password"] = hash_password(data.pop("password"))
        emp = Employee(**data)
        db.add(emp)
        db.commit()
        db.refresh(emp)
        return emp

    def get_employee(self, db: Session, employee_id: str) -> Optional[Employee]:
        return db.scalar(select(Employee).where(Employee.employee_id == employee_id))

    def list_employees(
        self,
        db: Session,
        q: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Tuple[List[Employee], int]:
        stmt = select(Employee)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                (Employee.name.ilike(like))
                | (Employee.email.ilike(like))
                | (Employee.employee_id.ilike(like))
                | (Employee.designation.ilike(like))
            )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Employee.id.desc())
        if limit is not None:
            stmt = stmt.offset(skip).limit(limit)
        rows = db.scalars(stmt).all()

        # 🔑 mypy-safe: force concrete list[Employee]
        employees: List[Employee] = cast(List[Employee], list(rows))
        return employees, int(total)

    def update_employee(
        self, db: Session, employee_id: str, payload: EmployeeUpdate
    ) -> Optional[Employee]:
        emp = db.scalar(select(Employee).where(Employee.employee_id == employee_id))
        if not emp:
            return None

        data = payload.dict(
            exclude_unset=True
        )  # Pydantic v2: payload.model_dump(exclude_unset=True)

        if "password" in data and data["password"] is not None:
            data["password"] = hash_password(data["password"])

        if "email" in data:
            dup = db.scalar(
                select(func.count())
                .select_from(Employee)
                .where(Employee.email == data["email"], Employee.id != emp.id)
            )
            if dup:
                raise ValueError("Email already exists")

        if "employee_id" in data:
            dup = db.scalar(
                select(func.count())
                .select_from(Employee)
                .where(Employee.employee_id == data["employee_id"], Employee.id != emp.id)
            )
            if dup:
                raise ValueError("Employee ID already exists")

        for k, v in data.items():
            setattr(emp, k, v)

        db.commit()
        db.refresh(emp)
        return emp

    def delete_employee(self, db: Session, employee_id: str) -> bool:
        emp = db.scalar(select(Employee).where(Employee.employee_id == employee_id))
        if not emp:
            return False
        db.delete(emp)
        db.commit()
        return True

    def get_employees_by_department(self, db: Session, department: Department) -> List[Employee]:
        stmt = select(Employee).where(Employee.department == department)
        rows = db.scalars(stmt).all()
        employees: List[Employee] = cast(List[Employee], list(rows))
        return employees

    def get_department_progress(self, db: Session, department: Department) -> dict:
        """Get progress metrics for all employees in a department"""
        from app.data.models.monthly_summary import MonthlyEmployeeSummary

        # Get all employees in department
        employees = self.get_employees_by_department(db, department)
        employee_ids = [emp.employee_id for emp in employees]

        if not employee_ids:
            return {"department": department.value, "total_employees": 0, "progress": []}

        # Get latest monthly summaries for these employees
        latest_summaries = (
            db.query(MonthlyEmployeeSummary)
            .filter(MonthlyEmployeeSummary.employee_id.in_(employee_ids))
            .order_by(MonthlyEmployeeSummary.employee_id, MonthlyEmployeeSummary.month_start.desc())
            .all()
        )

        # Group by employee_id to get latest summary per employee
        employee_summaries = {}
        for summary in latest_summaries:
            if summary.employee_id not in employee_summaries:
                employee_summaries[summary.employee_id] = summary

        # Calculate department totals
        total_employees = len(employees)
        total_present_days = sum(s.present_days for s in employee_summaries.values())
        total_work_days = sum(s.total_work_days for s in employee_summaries.values())
        total_worked_hours = sum(s.total_worked_hours for s in employee_summaries.values())
        total_overtime_hours = sum(s.overtime_hours for s in employee_summaries.values())
        total_leave_days = sum(s.leave_days for s in employee_summaries.values())

        # Calculate averages
        avg_attendance_rate = (
            (total_present_days / total_work_days * 100) if total_work_days > 0 else 0
        )
        avg_worked_hours = total_worked_hours / total_employees if total_employees > 0 else 0

        return {
            "department": department.value,
            "total_employees": total_employees,
            "total_present_days": total_present_days,
            "total_work_days": total_work_days,
            "total_worked_hours": total_worked_hours,
            "total_overtime_hours": total_overtime_hours,
            "total_leave_days": total_leave_days,
            "average_attendance_rate": round(avg_attendance_rate, 2),
            "average_worked_hours": round(avg_worked_hours, 2),
        }

    def get_all_employees_by_department(self, db: Session) -> dict:
        """Get all employees grouped by department"""
        from app.data.models.add_employee import Department

        result = {}
        for dept in Department:
            employees = self.get_employees_by_department(db, dept)
            if employees:  # Only include departments with employees
                result[dept.value] = [EmployeeRead.model_validate(emp) for emp in employees]
        return result
