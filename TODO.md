# TODO: Remove Payroll Process

## Files to Delete
- [x] app/data/models/payroll.py
- [x] app/schemas/payperiod.py
- [x] app/schemas/payroll_run.py
- [x] app/schemas/payroll_item.py
- [x] app/schemas/employee_salary.py
- [x] app/data/repositories/payroll_repository.py
- [x] app/services/payroll_service.py
- [x] app/routes/admin_payroll_router.py
- [x] app/routes/employee_payroll_router.py
- [x] app/controllers/admin_payroll_controller.py
- [x] app/controllers/employee_payroll_controller.py

## Files to Edit
- [x] app/api/main.py: Remove payroll router imports and includes

## Database Changes
- [x] Create Alembic migration to drop payroll tables (payroll_items, payroll_runs, pay_periods, employee_salary) and remove payroll-related columns from employees (bank_name, ifsc_code) and employee_salary (pf_scheme, esi_scheme, gratuity_scheme)
