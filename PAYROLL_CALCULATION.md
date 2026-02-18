# Payroll Calculation System - Documentation

## Overview

The payroll calculation system integrates three key components:
1. **Employee Salary** - Base salary and payroll policy assignment
2. **Payroll Policy** - Rules for allowances and deductions
3. **Attendance Data** - Worked hours, overtime, absences, and leave

## Architecture

### Core Models

```
Employee
├── EmployeeSalary (current base_salary, gross_salary, policy assignment)
│   ├── SalaryBreakdown (audit trail of applied rules)
│   └── PayrollPolicy (used during calculation)
│       └── PayrollPolicyRule (individual allowances/deductions)
│
└── AttendanceDay (daily work records)
    └── MonthlyEmployeeSummary (rolled-up monthly metrics)
```

### Data Flow

```
Employee Base Salary
       ↓
   + Policy Rules (allowances/deductions)
       ↓
   + Attendance Metrics (overtime, absences)
       ↓
   = Gross Salary
       ↓
   SalaryBreakdown (recorded for audit)
```

## Policy Rules

### Rule Types

- **ALLOWANCE**: Increases gross salary (bonuses, allowances, overtime pay)
- **DEDUCTION**: Decreases gross salary (tax, insurance, absence penalties)

### Value Types

- **Percentage**: Calculated as `(base_salary * rule.value / 100)`
- **Flat Amount**: Applied directly as `rule.value`

### Applies To

Rules can target different metrics via the `applies_to` field:

| Value | Description | Example |
|-------|-------------|---------|
| `fixed` | Applied to base salary | Transport allowance, lunch allowance |
| `overtime` | Per hour of overtime | Extra ₹500 per overtime hour |
| `unpaid_leave` | Per hour of unpaid leave | ₹400 per unpaid leave hour deduction |
| `underwork` | Per hour of underwork (< expected) | ₹200 per underwork hour deduction |
| `attendance_bonus` | Based on present days | Fixed amount or per-day bonus |
| `gross` | Applied to calculated gross | Percentage-based tax or bonus |

## Calculation Flow

### Step 1: Load Employee Data
```
Employee → Base Salary → Policy → Rules
```

### Step 2: Load Attendance Data
```
AttendanceDay records → MonthlyEmployeeSummary (roll-up)
```

### Step 3: Apply Rules
```
For each rule in policy:
  1. Determine amount based on rule type and applies_to
  2. Add to allowances or deductions
  3. Update gross salary
```

### Step 4: Create Breakdown
```
SalaryBreakdown entries created for each applied rule
(for audit trail and reporting)
```

## API Endpoints

### 1. Calculate Payroll for Single Employee
```
GET /api/payroll/calculation/employee/{employee_id}
?month_start=2026-02-01

Response:
{
  "employee_id": 1,
  "employee_code": "EMP001",
  "month_start": "2026-02-01",
  "salary": {
    "base": 50000,
    "gross": 52500,
    "net": 52500
  },
  "attendance": {
    "present_days": 20,
    "total_work_days": 22,
    "worked_hours": 168.5,
    "overtime_hours": 8.5,
    "underwork_hours": 0,
    "paid_leave_hours": 8,
    "unpaid_leave_hours": 0
  },
  "policy": {
    "id": 1,
    "name": "Standard IT Policy"
  },
  "breakdown": {
    "allowances": [
      {
        "rule_name": "DA (Dearness Allowance)",
        "is_percentage": true,
        "value": 10.0,
        "amount": 5000.0,
        "applies_to": "fixed"
      },
      {
        "rule_name": "Overtime Pay",
        "is_percentage": false,
        "value": 500.0,
        "amount": 4250.0,
        "applies_to": "overtime"
      }
    ],
    "deductions": [
      {
        "rule_name": "Income Tax",
        "is_percentage": true,
        "value": 5.0,
        "amount": 2625.0,
        "applies_to": "gross"
      }
    ],
    "attendance_adjustments": [
      {
        "name": "Overtime Pay",
        "type": "overtime",
        "hours": 8.5,
        "rate": 500.0,
        "amount": 4250.0
      }
    ]
  }
}
```

### 2. Calculate Payroll for All Employees
```
GET /api/payroll/calculation/all
?month_start=2026-02-01

Response:
[
  { ... payroll calculation ... },
  { ... payroll calculation ... },
  ...
]
```

### 3. Generate/Update Salary Record
```
POST /api/payroll/generate/employee/{employee_id}
?month_start=2026-02-01

Response:
{
  "id": 5,
  "employee_id": 1,
  "base_salary": 50000,
  "gross_salary": 52500,
  "payroll_policy_id": 1,
  "breakdowns": [
    {
      "rule_name": "DA (Dearness Allowance)",
      "rule_type": "ALLOWANCE",
      "applies_to": "fixed",
      "amount": 5000.0
    },
    ...
  ]
}
```

### 4. Generate Salaries for All Employees
```
POST /api/payroll/generate/all
?month_start=2026-02-01

Response:
{
  "month": "2026-02-01",
  "generated": 15,
  "failed": 0,
  "results": [
    {
      "employee_id": 1,
      "employee_code": "EMP001",
      "gross_salary": 52500,
      "status": "success"
    },
    ...
  ],
  "errors": []
}
```

## Usage Examples

### Example: IT Company with Overtime & Attendance Tracking

**Policy: "Standard IT Policy"**

| Rule Name | Type | Applies To | Value | Notes |
|-----------|------|-----------|-------|-------|
| Dearness Allowance | ALLOWANCE | fixed | 10% | Basic cost-of-living |
| Transport Allowance | ALLOWANCE | fixed | 2000 | Flat amount |
| Overtime Pay | ALLOWANCE | overtime | 500 | ₹500 per hour |
| Attendance Bonus | ALLOWANCE | attendance_bonus | 1000 | Per present day |
| Income Tax | DEDUCTION | gross | 5% | Applied to gross |
| Health Insurance | DEDUCTION | fixed | 1500 | Flat deduction |

**Employee Calculation (Feb 2026):**

```
Base Salary:                           ₹50,000

Allowances:
  + DA (10% of 50000)                 ₹5,000
  + Transport                          ₹2,000
  + Overtime (8.5 hrs × ₹500)         ₹4,250
  + Attendance Bonus (20 days × ₹1000) ₹20,000
                                      --------
  Gross Before Deductions:            ₹81,250

Deductions:
  - Income Tax (5% of 81250)          ₹4,062.50
  - Health Insurance                   ₹1,500
                                      -----------
Net Salary:                           ₹75,687.50
```

## Implementation Details

### PayrollCalculation Class

Represents one payroll calculation with:
- Employee info
- Salary components (base, gross, net)
- Attendance metrics
- Breakdown of allowances, deductions, adjustments

### Key Functions

**`get_payroll_for_employee(db, employee_id, month_start)`**
- Loads employee, salary, attendance, and policy
- Calculates all components
- Returns PayrollCalculation object

**`get_payroll_for_all_employees(db, month_start)`**
- Calls above for all employees
- Returns list of calculations

**`generate_salary_breakdown(db, employee_id, month_start)`**
- Creates/updates EmployeeSalary record
- Generates SalaryBreakdown entries
- Persists to database for audit trail

## Extending the System

### Adding New Attendance Metrics

1. Ensure `MonthlyEmployeeSummary` has the field
2. Add condition in `_apply_policy_rules()`:

```python
elif summary and applies_to == "new_metric":
    amount = rule.value * summary.new_metric_field
    calc.attendance_adjustments.append({...})
```

3. Document the new `applies_to` value

### Adding New Rule Properties

Create new enum in `PayrollPolicyRule`:

```python
class RuleScope(str, Enum):
    ALLOWANCE = "ALLOWANCE"
    DEDUCTION = "DEDUCTION"
```

Then reference in calculation logic.

## Audit Trail

Every calculated payroll is recorded:
1. **EmployeeSalary** - Snapshot of base/gross salary
2. **SalaryBreakdown** - Line items showing each rule applied
3. **Date** - Linked to specific month for historical tracking

This enables:
- Policy change audits ("What changed?")
- Payroll verification ("Why this amount?")
- Reporting ("Overtime trends", "Attendance patterns")

## Best Practices

1. **Monthly Snapshots**: Generate payroll at month-end after attendance is finalized
2. **Lock Records**: Consider adding `lock_flag` to EmployeeSalary to prevent accidental updates
3. **Approval Workflow**: Add approval status before final payment processing
4. **Batch Jobs**: Use `/payroll/generate/all` in scheduled jobs (cron/APScheduler)
5. **Validation**: Verify attendance summary is complete before calculating

## Common Scenarios

### Scenario 1: Absence Deduction
Employee absent 2 days (unpaid leave):
- Set rule: `applies_to="unpaid_leave", value=500` (₹500 per hour deduction)
- AttendanceDay records unpaid hours
- Calculation deducts automatically

### Scenario 2: Performance Bonus
Add rule: `applies_to="fixed", value=5000` (ALLOWANCE)
- Always applied, not based on attendance

### Scenario 3: Percentage Tax
Add rule: `applies_to="gross", value=10%` (DEDUCTION, is_percentage=true)
- Calculated against final gross after all additions

### Scenario 4: Shift Incentive
Add rule: `applies_to="shift", value=2000` (ALLOWANCE)
- Would require `MonthlyEmployeeSummary.shift_type` field
- Then apply based on shift assignment
