"""Add paid_leave_days and unpaid_leave_days to monthly_employee_summaries

Revision ID: 193de0c1b81a
Revises: d0bba1850392
Create Date: 2025-11-28 12:40:29.062507
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "193de0c1b81a"
down_revision: Union[str, Sequence[str], None] = "d0bba1850392"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "monthly_employee_summaries",
        sa.Column("paid_leave_days", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "monthly_employee_summaries",
        sa.Column("unpaid_leave_days", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("monthly_employee_summaries", "paid_leave_days")
    op.drop_column("monthly_employee_summaries", "unpaid_leave_days")
