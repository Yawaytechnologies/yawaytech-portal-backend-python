from app.data.repositories import shift_grace_policy_repository as shift_grace_policy


def create_policy_service(db, policy_data):
    if policy_data.excused_minutes > 120:
        raise ValueError("Excused minutes cannot exceed 120")
    return shift_grace_policy.create_policy(db, policy_data)


def update_policy_service(db, policy_id, updates):
    return shift_grace_policy.update_policy(db, policy_id, updates)


def list_policies_service(db, shift_id=None):
    return shift_grace_policy.list_policies(db, shift_id)


def delete_policy_service(db, policy_id):
    return shift_grace_policy.delete_policy(db, policy_id)
