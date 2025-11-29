"""Add pending_leave_days to monthly_employee_summaries

Revision ID: a1b2c3d4e5f6
Revises: 193de0c1b81a
Create Date: 2025-11-28 15:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '193de0c1b81a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "monthly_employee_summaries",
        sa.Column("pending_leave_days", sa.Integer(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("monthly_employee_summaries", "pending_leave_days")
