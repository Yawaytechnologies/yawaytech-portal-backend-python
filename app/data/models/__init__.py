# app/data/models/__init__.py
from app.data.models.add_employee import Employee
from app.data.models.policy import WorkweekPolicy, HolidayCalendar
from app.data.models.shifts import Shift, EmployeeShiftAssignment
from app.data.models.leave import LeaveType, LeaveRequest, LeaveBalance
from app.data.models.admin import Admin
from app.data.models.expenses import Expense
from app.data.models.shift_grace_policy import ShiftGracePolicy
from app.data.models.employee_bank_detail import EmployeeBankDetail

# from app.data.models.payroll import EmployeeSalary, PayPeriod, PayrollRun, PayrollItem  # Commented out as payroll is removed

# Re-export attendance models from the features module
from app.data.models.attendance import (
    AttendanceSession,
    AttendanceDay,
    CheckInMonitoring,
)

__all__ = [
    "Employee",
    "WorkweekPolicy",
    "HolidayCalendar",
    "Shift",
    "EmployeeShiftAssignment",
    "LeaveType",
    "LeaveRequest",
    "LeaveBalance",
    # "EmployeeSalary",  # Commented out as payroll is removed
    # "PayPeriod",  # Commented out as payroll is removed
    # "PayrollRun",  # Commented out as payroll is removed
    # "PayrollItem",  # Commented out as payroll is removed
    "AttendanceSession",
    "AttendanceDay",
    "CheckInMonitoring",
    "Admin",
    "Expense",
    "ShiftGracePolicy",
    "EmployeeBankDetail",
]
