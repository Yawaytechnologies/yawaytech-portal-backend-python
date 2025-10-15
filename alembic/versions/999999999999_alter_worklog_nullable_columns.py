"""Alter worklog columns to nullable

Revision ID: 999999999999
Revises: a05ef679ed18
Create Date: 2025-10-04 12:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "999999999999"
down_revision = "a05ef679ed18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("worklogs", "start_time", nullable=True)
    op.alter_column("worklogs", "end_time", nullable=True)
    op.alter_column("worklogs", "work_date", nullable=True)
    op.alter_column("worklogs", "work_type", nullable=True)


def downgrade() -> None:
    op.alter_column("worklogs", "start_time", nullable=False)
    op.alter_column("worklogs", "end_time", nullable=False)
    op.alter_column("worklogs", "work_date", nullable=False)
    op.alter_column("worklogs", "work_type", nullable=False)
