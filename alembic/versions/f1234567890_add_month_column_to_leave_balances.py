"""add month column to leave_balances

Revision ID: f1234567890
Revises: eaa9557d0334
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1234567890"
down_revision: Union[str, Sequence[str], None] = "eaa9557d0334"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leave_balances", sa.Column("month", sa.Integer(), nullable=True))
    # Update unique constraint to include month
    op.drop_constraint("uq_leave_balance_emp_type_year", "leave_balances", type_="unique")
    op.create_unique_constraint(
        "uq_leave_balance_emp_type_year_month",
        "leave_balances",
        ["employee_id", "leave_type_id", "year", "month"],
    )
    # Update index
    op.drop_index("ix_leave_balance_emp_year", table_name="leave_balances")
    op.create_index(
        "ix_leave_balance_emp_year_month",
        "leave_balances",
        ["employee_id", "year", "month"],
    )


def downgrade() -> None:
    # Revert index
    op.drop_index("ix_leave_balance_emp_year_month", table_name="leave_balances")
    op.create_index(
        "ix_leave_balance_emp_year",
        "leave_balances",
        ["employee_id", "year"],
    )
    # Revert unique constraint
    op.drop_constraint("uq_leave_balance_emp_type_year_month", "leave_balances", type_="unique")
    op.create_unique_constraint(
        "uq_leave_balance_emp_type_year",
        "leave_balances",
        ["employee_id", "leave_type_id", "year"],
    )
    op.drop_column("leave_balances", "month")
