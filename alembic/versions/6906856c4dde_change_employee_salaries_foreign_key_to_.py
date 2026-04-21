"""change employee_salaries foreign key to employee_id

Revision ID: 6906856c4dde
Revises: 0525888c2c6c
Create Date: 2026-03-18 15:17:02.865751

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6906856c4dde"
down_revision: Union[str, Sequence[str], None] = "0525888c2c6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop foreign key from employee_salaries
    op.drop_constraint(
        "employee_salaries_payroll_policy_id_fkey", "employee_salaries", type_="foreignkey"
    )

    # Drop foreign key from payroll_policy_rules
    op.drop_constraint(
        "payroll_policy_rules_payroll_policy_id_fkey", "payroll_policy_rules", type_="foreignkey"
    )

    # Now drop the table safely
    op.drop_table("payroll_policies")
