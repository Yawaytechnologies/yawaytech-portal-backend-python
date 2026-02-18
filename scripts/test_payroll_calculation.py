#!/usr/bin/env python3
# scripts/test_payroll_calculation.py
"""
Test and demonstrate the payroll calculation system.

This script shows how employee salaries are calculated based on:
1. Attendance data (worked hours, overtime, absences)
2. Base salary
3. Payroll policy rules
"""

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.data.db import SessionLocal
from app.data.models.add_employee import Employee, Department, MaritalStatus
from app.data.models.employee_salary import EmployeeSalary
from app.data.models.payroll_policy import PayrollPolicy
from app.data.models.payroll_policy_rule import PayrollPolicyRule, Ruletypes
from app.data.models.attendance import AttendanceDay, DayStatus
from app.data.models.monthly_summary import MonthlyEmployeeSummary
from app.services.payroll_calculator_service import get_payroll_for_employee


def create_test_payroll_setup(db: Session):
    """
    Create sample data for testing payroll calculations.
    """
    print("\n" + "="*80)
    print("CREATING TEST PAYROLL SETUP")
    print("="*80)
    
    # 1. Create/find an employee
    employee = db.query(Employee).filter(Employee.employee_id == "EMP001").first()
    if not employee:
        from app.data.models.add_employee import Department, MaritalStatus
        employee = Employee(
            employee_id="EMP001",
            name="John Doe",
            father_name="Richard Doe",
            email="john@example.com",
            mobile_number="9876543210",
            date_of_birth=date(1990, 5, 15),
            date_of_joining=date(2022, 1, 1),
            designation="Senior Developer",
            department=Department.IT,
            permanent_address="123 Main Street, City, Country",
            marital_status=MaritalStatus.SINGLE,
            password="hashed_password",
        )
        db.add(employee)
        db.flush()
        print(f"[OK] Created employee: {employee.employee_id}")
    else:
        print(f"[OK] Found existing employee: {employee.employee_id}")
    
    # 2. Create payroll policy
    policy = db.query(PayrollPolicy).filter(PayrollPolicy.name == "IT Standard Policy").first()
    if not policy:
        policy = PayrollPolicy(
            name="IT Standard Policy",
            description="Standard payroll policy for IT department employees",
            effective_from=date(2026, 1, 1),
            effective_to=None,
            is_active=True,
        )
        db.add(policy)
        db.flush()
        print(f"✓ Created policy: {policy.name}")
    else:
        print(f"✓ Found existing policy: {policy.name}")
    
    # 3. Create/update policy rules
    rule_configs = [
        {
            "rule_name": "Dearness Allowance",
            "rule_type": Ruletypes.ALLOWANCE,
            "is_percentage": True,
            "value": 10.0,
            "applies_to": "fixed",
            "description": "10% of base salary",
        },
        {
            "rule_name": "Transport Allowance",
            "rule_type": Ruletypes.ALLOWANCE,
            "is_percentage": False,
            "value": 2000.0,
            "applies_to": "fixed",
            "description": "Fixed monthly transport allowance",
        },
        {
            "rule_name": "Overtime Pay",
            "rule_type": Ruletypes.ALLOWANCE,
            "is_percentage": False,
            "value": 500.0,
            "applies_to": "overtime",
            "description": "₹500 per hour of overtime",
        },
        {
            "rule_name": "Attendance Bonus",
            "rule_type": Ruletypes.ALLOWANCE,
            "is_percentage": False,
            "value": 1000.0,
            "applies_to": "attendance_bonus",
            "description": "₹1000 per present day",
        },
        {
            "rule_name": "Income Tax",
            "rule_type": Ruletypes.DEDUCTION,
            "is_percentage": True,
            "value": 5.0,
            "applies_to": "gross",
            "description": "5% income tax on gross",
        },
        {
            "rule_name": "Health Insurance",
            "rule_type": Ruletypes.DEDUCTION,
            "is_percentage": False,
            "value": 1500.0,
            "applies_to": "fixed",
            "description": "Monthly health insurance premium",
        },
    ]
    
    # Clear existing rules
    policy.rules.clear()
    
    for config in rule_configs:
        rule = PayrollPolicyRule(
            rule_name=config["rule_name"],
            rule_type=config["rule_type"],
            is_percentage=config["is_percentage"],
            value=config["value"],
            applies_to=config["applies_to"],
            is_enabled=True,
        )
        policy.rules.append(rule)
    
    print(f"✓ Created {len(rule_configs)} policy rules")
    
    # 4. Create employee salary
    salary = db.query(EmployeeSalary).filter(EmployeeSalary.employee_id == employee.id).first()
    if not salary:
        salary = EmployeeSalary(
            employee_id=employee.id,
            base_salary=50000.0,
            gross_salary=50000.0,  # Will be recalculated
            payroll_policy_id=policy.id,
        )
        db.add(salary)
        db.flush()
        print(f"✓ Created employee salary: ₹{salary.base_salary}")
    else:
        salary.base_salary = 50000.0
        salary.payroll_policy_id = policy.id
        print(f"✓ Updated employee salary: ₹{salary.base_salary}")
    
    # 5. Create test attendance data for February 2026
    month_start = date(2026, 2, 1)
    
    # Clear existing attendance for this month
    db.query(AttendanceDay).filter(
        AttendanceDay.employee_id == employee.employee_id,
        AttendanceDay.work_date_local >= month_start,
        AttendanceDay.work_date_local < date(2026, 3, 1),
    ).delete()
    
    # Create attendance days
    attendance_count = 0
    for day_offset in range(28):  # 28 days of Feb
        work_date = month_start + timedelta(days=day_offset)
        
        # Skip weekends (Saturday=5, Sunday=6)
        if work_date.weekday() >= 5:
            status = DayStatus.WEEKEND
            seconds = 0
        # Create a couple of overtime days
        elif day_offset in [5, 12, 19]:
            status = DayStatus.PRESENT
            seconds = 10 * 3600  # 10 hours (2 hours overtime)
        # One unpaid leave day
        elif day_offset == 10:
            status = DayStatus.ABSENT
            seconds = 0
        # Normal work days
        else:
            status = DayStatus.PRESENT
            seconds = 8 * 3600  # 8 hours
        
        att_day = AttendanceDay(
            employee_id=employee.employee_id,
            work_date_local=work_date,
            seconds_worked=seconds,
            expected_seconds=28800,  # 8 hours
            status=status,
        )
        db.add(att_day)
        attendance_count += 1
    
    print(f"✓ Created {attendance_count} attendance day records")
    
    # 6. Create monthly summary
    summary = db.query(MonthlyEmployeeSummary).filter(
        MonthlyEmployeeSummary.employee_id == employee.employee_id,
        MonthlyEmployeeSummary.month_start == month_start,
    ).first()
    
    if not summary:
        summary = MonthlyEmployeeSummary(
            employee_id=employee.employee_id,
            month_start=month_start,
            total_work_days=22,  # Excluding weekends
            present_days=20,
            holiday_days=0,
            weekend_days=8,
            leave_days=1,
            paid_leave_hours=0,
            unpaid_leave_hours=8,  # One day absence
            pending_leave_hours=0,
            paid_leave_days=0,
            unpaid_leave_days=1,
            pending_leave_days=0,
            total_worked_hours=168.0,  # 20 days × 8 hours + 2 hours overtime
            expected_hours=176.0,  # 22 days × 8 hours
            overtime_hours=2.0,  # From 3 overtime days
            underwork_hours=0,
        )
        db.add(summary)
        print(f"✓ Created monthly summary for {month_start}")
    
    db.commit()
    print("\n✓ Test setup complete!\n")
    return employee, salary, policy, summary


def display_payroll_calculation(employee: Employee, payroll):
    """Display detailed payroll calculation."""
    print("\n" + "="*80)
    print(f"PAYROLL CALCULATION: {employee.name} ({employee.employee_id})")
    print(f"Month: {payroll['month_start']}")
    print("="*80)
    
    # Salary summary
    print("\n📊 SALARY SUMMARY")
    print(f"  Base Salary:           ₹{payroll['salary']['base']:>10,.2f}")
    print(f"  Gross Salary:          ₹{payroll['salary']['gross']:>10,.2f}")
    print(f"  Net Salary:            ₹{payroll['salary']['net']:>10,.2f}")
    
    # Attendance
    print("\n📅 ATTENDANCE (Feb 2026)")
    att = payroll['attendance']
    print(f"  Present Days:          {att['present_days']:>10} days")
    print(f"  Total Work Days:       {att['total_work_days']:>10} days")
    print(f"  Worked Hours:          {att['worked_hours']:>10.1f} hours")
    print(f"  Expected Hours:        {att['expected_hours']:>10.1f} hours")
    print(f"  Overtime Hours:        {att['overtime_hours']:>10.1f} hours")
    print(f"  Underwork Hours:       {att['underwork_hours']:>10.1f} hours")
    print(f"  Paid Leave Hours:      {att['paid_leave_hours']:>10.1f} hours")
    print(f"  Unpaid Leave Hours:    {att['unpaid_leave_hours']:>10.1f} hours")
    
    # Policy
    print("\n📋 PAYROLL POLICY")
    policy = payroll['policy']
    print(f"  Policy Name:           {policy['name']}")
    print(f"  Policy ID:             {policy['id']}")
    
    # Breakdown
    breakdown = payroll['breakdown']
    
    if breakdown['allowances']:
        print("\n✅ ALLOWANCES")
        total_allow = 0
        for allow in breakdown['allowances']:
            amount = allow['amount']
            total_allow += amount
            is_pct = "(%)" if allow['is_percentage'] else "flat"
            print(f"  {allow['rule_name']:<30} ₹{amount:>10,.2f}  [{is_pct}]")
        print(f"  {'Total Allowances':<30} ₹{total_allow:>10,.2f}")
    
    if breakdown['deductions']:
        print("\n❌ DEDUCTIONS")
        total_ded = 0
        for ded in breakdown['deductions']:
            amount = ded['amount']
            total_ded += amount
            is_pct = "(%)" if ded['is_percentage'] else "flat"
            print(f"  {ded['rule_name']:<30} ₹{amount:>10,.2f}  [{is_pct}]")
        print(f"  {'Total Deductions':<30} ₹{total_ded:>10,.2f}")
    
    if breakdown['attendance_adjustments']:
        print("\n⏰ ATTENDANCE-BASED ADJUSTMENTS")
        for adj in breakdown['attendance_adjustments']:
            print(f"  {adj['name']:<30}")
            print(f"    Type:                  {adj['type']}")
            for key in ['hours', 'present_days', 'rate']:
                if key in adj:
                    print(f"    {key.capitalize()}:          {adj[key]}")
            print(f"    Amount:                ₹{adj['amount']:>10,.2f}")
    
    print("\n" + "="*80 + "\n")


def main():
    """Main test function."""
    db = SessionLocal()
    
    try:
        # Setup test data
        employee, salary, policy, summary = create_test_payroll_setup(db)
        
        # Calculate payroll
        print("\n🔄 CALCULATING PAYROLL...")
        payroll = get_payroll_for_employee(
            db,
            employee.id,
            date(2026, 2, 1)
        )
        
        if payroll:
            display_payroll_calculation(employee, payroll.to_dict())
            
            print("\n✨ KEY INSIGHTS:")
            print(f"  - {payroll.present_days} out of {payroll.total_work_days} work days present")
            print(f"  - {payroll.overtime_hours:.1f} hours of overtime worked")
            print(f"  - Overtime bonus: ₹{payroll.overtime_hours * 500:,.2f}")
            print(f"  - Attendance bonus: ₹{payroll.present_days * 1000:,.2f}")
            print(f"  - Total additions: ₹{payroll.base_salary - salary.base_salary + sum(a['amount'] for a in payroll.allowances):,.2f}")
        else:
            print("❌ Failed to calculate payroll")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
