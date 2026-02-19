from app.data.db import SessionLocal
from app.data.models.payroll_policy import PayrollPolicy

db = SessionLocal()
policy = db.query(PayrollPolicy).first()
if policy:
    print("Policy:", policy.name)
    for rule in policy.rules:
        print(f"  Rule: {rule.rule_name}")
        print(f"    rule_type: {rule.rule_type}")
        print(f"    rule_type type: {type(rule.rule_type)}")
        print(f"    rule_type str: {str(rule.rule_type)}")
        if hasattr(rule.rule_type, "value"):
            print(f"    rule_type.value: {rule.rule_type.value}")
            print(f'    Equals ALLOWANCE? {rule.rule_type.value == "ALLOWANCE"}')
db.close()
