# Fix Mypy Errors

## Errors to Fix:
1. app/data/models/payroll_policy_rule.py:15 - Need type annotation for "rule_type"
2. app/services/employeee_salary_service.py:32 & 61 - Argument 2 incompatible type "PayrollPolicy | None"; expected "PayrollPolicy"
3. app/data/repositories/shift_grace_policy_repository.py:14 - Name "Optional" is not defined
4. app/routes/payroll_policy_router.py:27 - Argument 3 incompatible type "PayrollPolicyBase"; expected "PayrollPolicyUpdate"
5. app/controllers/shift_grace_policy_controller.py:28 - Name "Optional" is not defined
6. app/routes/shift_grace_policy_router.py:28 - Name "Optional" is not defined
7. app/services/policy_service.py:31 - "PolicyRepository" has no attribute "create_workweek"
8. app/routes/leave_admin_router.py:77 - Argument 4 incompatible type "list[BalanceSeedItem]"; expected "list[dict[Any, Any]]"

## Plan:
- Update payroll_policy_rule.py to use Mapped[Ruletypes] for rule_type
- Modify employeee_salary_service.py to accept Optional[PayrollPolicy] and handle None
- Add import for Optional in shift_grace_policy_repository.py
- Fix payroll_policy_router.py to use PayrollPolicyUpdate
- Add import for Optional in shift_grace_policy_controller.py and router
- Change create_workweek to upsert_workweek in policy_service.py
- Convert BalanceSeedItem list to dict list in leave_admin_router.py
