"""add monthly_employee_summaries table

Revision ID: d0bba1850392
Revises: 23a3f9bb26fd
Create Date: 2025-11-26 17:48:47.577297
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d0bba1850392"
down_revision: Union[str, Sequence[str], None] = "23a3f9bb26fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monthly_employee_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.String(length=9), nullable=False),
        sa.Column("month_start", sa.Date(), nullable=False),

        # Attendance counts
        sa.Column("total_work_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("present_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("holiday_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("weekend_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("leave_days", sa.Integer(), nullable=False, server_default="0"),

        # Leave breakdown
        sa.Column("paid_leave_hours", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("unpaid_leave_hours", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("pending_leave_hours", sa.Numeric(8, 2), nullable=False, server_default="0"),

        # Work metrics
        sa.Column("total_worked_hours", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("expected_hours", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("overtime_hours", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("underwork_hours", sa.Numeric(10, 2), nullable=False, server_default="0"),

        # JSON breakdown
        sa.Column("leave_type_breakdown", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),

        # Audit
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        sa.UniqueConstraint("employee_id", "month_start", name="uq_monthly_summary_emp_month"),
    )

    op.create_index(
        "ix_monthly_summary_emp_month",
        "monthly_employee_summaries",
        ["employee_id", "month_start"],
    )


def downgrade() -> None:
    op.drop_index("ix_monthly_summary_emp_month", table_name="monthly_employee_summaries")
    op.drop_table("monthly_employee_summaries")