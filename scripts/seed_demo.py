#!/usr/bin/env python3
"""
Seed demo data into the database.
Run this script from the project root: python scripts/seed_demo.py
"""

import sys
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from app.data.db import engine, Base, SessionLocal
from app.data.models.add_employee import Employee, MaritalStatus, Department
from app.data.models.expenses import Expense
from app.data.models.admin import Admin
from app.data.models.attendance import AttendanceSession, AttendanceDay
from app.core.security import hash_password

# Use local SQLite for demo seeding (comment out to use env DATABASE_URL)
os.environ["DATABASE_URL"] = "sqlite:///dev.db"

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Print database URL for verification
print("DATABASE_URL:", os.getenv("DATABASE_URL"))


def seed_data():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed Admin
        admin_password = hash_password("admin123")
        admin = Admin(
            admin_id="admin",
            password_hash=admin_password,
            is_active=True,
            is_super_admin=True,
        )
        db.add(admin)
        print("Seeded admin")

        # Seed Employees
        employees_data = [
            {
                "name": "John Doe",
                "father_name": "Robert Doe",
                "employee_id": "EMP001",
                "date_of_joining": date(2023, 1, 15),
                "email": "john.doe@example.com",
                "mobile_number": "9876543210",
                "marital_status": MaritalStatus.SINGLE,
                "date_of_birth": date(1990, 5, 20),
                "permanent_address": "123 Main St, City, State",
                "designation": "Software Engineer",
                "department": Department.IT,
                "password": hash_password("password123"),
            },
            {
                "name": "Jane Smith",
                "father_name": "Michael Smith",
                "employee_id": "EMP002",
                "date_of_joining": date(2023, 2, 10),
                "email": "jane.smith@example.com",
                "mobile_number": "9876543211",
                "marital_status": MaritalStatus.MARRIED,
                "date_of_birth": date(1985, 8, 15),
                "permanent_address": "456 Oak Ave, City, State",
                "designation": "HR Manager",
                "department": Department.HR,
                "password": hash_password("password123"),
            },
            {
                "name": "Bob Johnson",
                "father_name": "David Johnson",
                "employee_id": "EMP003",
                "date_of_joining": date(2023, 3, 5),
                "email": "bob.johnson@example.com",
                "mobile_number": "9876543212",
                "marital_status": MaritalStatus.SINGLE,
                "date_of_birth": date(1992, 12, 10),
                "permanent_address": "789 Pine Rd, City, State",
                "designation": "Sales Executive",
                "department": Department.SALES,
                "password": hash_password("password123"),
            },
        ]

        employees = []
        for emp_data in employees_data:
            emp = Employee(**emp_data)
            db.add(emp)
            employees.append(emp)
        db.commit()  # Commit to get IDs
        print("Seeded employees")

        # Seed Expenses
        expenses_data = [
            {
                "title": "Office Supplies",
                "amount": 150.00,
                "category": "Office",
                "date": date.today() - timedelta(days=5),
                "description": "Bought pens and paper",
                "added_by": "EMP001",
            },
            {
                "title": "Team Lunch",
                "amount": 200.00,
                "category": "Food",
                "date": date.today() - timedelta(days=3),
                "description": "Lunch for project team",
                "added_by": "EMP002",
            },
            {
                "title": "Travel to Conference",
                "amount": 500.00,
                "category": "Travel",
                "date": date.today() - timedelta(days=10),
                "description": "Flight and hotel",
                "added_by": "EMP001",
            },
            {
                "title": "Software License",
                "amount": 300.00,
                "category": "Software",
                "date": date.today() - timedelta(days=7),
                "description": "Annual license renewal",
                "added_by": "EMP003",
            },
        ]

        for exp_data in expenses_data:
            exp = Expense(**exp_data)
            db.add(exp)
        print("Seeded expenses")

        # Seed Attendance
        # For simplicity, seed for today and yesterday
        today = date.today()
        yesterday = today - timedelta(days=1)

        attendance_data = [
            # John Doe - today
            {
                "employee_id": "EMP001",
                "check_in_utc": datetime.combine(today, datetime.min.time().replace(hour=9)),
                "check_out_utc": datetime.combine(today, datetime.min.time().replace(hour=17)),
                "work_date_local": today,
            },
            # Jane Smith - today
            {
                "employee_id": "EMP002",
                "check_in_utc": datetime.combine(
                    today, datetime.min.time().replace(hour=8, minute=30)
                ),
                "check_out_utc": datetime.combine(
                    today, datetime.min.time().replace(hour=16, minute=30)
                ),
                "work_date_local": today,
            },
            # Bob Johnson - yesterday
            {
                "employee_id": "EMP003",
                "check_in_utc": datetime.combine(
                    yesterday, datetime.min.time().replace(hour=9, minute=15)
                ),
                "check_out_utc": datetime.combine(
                    yesterday, datetime.min.time().replace(hour=17, minute=45)
                ),
                "work_date_local": yesterday,
            },
        ]

        for att_data in attendance_data:
            session = AttendanceSession(**att_data)
            db.add(session)
        db.commit()  # Commit sessions first

        # Now seed AttendanceDay (rollup)
        # For today
        day_today = AttendanceDay(
            employee_id="EMP001",
            work_date_local=today,
            seconds_worked=8 * 3600,  # 8 hours
            first_check_in_utc=datetime.combine(today, datetime.min.time().replace(hour=9)),
            last_check_out_utc=datetime.combine(today, datetime.min.time().replace(hour=17)),
            status="PRESENT",
        )
        db.add(day_today)

        day_today2 = AttendanceDay(
            employee_id="EMP002",
            work_date_local=today,
            seconds_worked=8 * 3600,
            first_check_in_utc=datetime.combine(
                today, datetime.min.time().replace(hour=8, minute=30)
            ),
            last_check_out_utc=datetime.combine(
                today, datetime.min.time().replace(hour=16, minute=30)
            ),
            status="PRESENT",
        )
        db.add(day_today2)

        # For yesterday
        day_yesterday = AttendanceDay(
            employee_id="EMP003",
            work_date_local=yesterday,
            seconds_worked=8 * 3600 + 30 * 60,  # approx
            first_check_in_utc=datetime.combine(
                yesterday, datetime.min.time().replace(hour=9, minute=15)
            ),
            last_check_out_utc=datetime.combine(
                yesterday, datetime.min.time().replace(hour=17, minute=45)
            ),
            status="PRESENT",
        )
        db.add(day_yesterday)

        db.commit()
        print("Seeded attendance")

        print("Demo data seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
