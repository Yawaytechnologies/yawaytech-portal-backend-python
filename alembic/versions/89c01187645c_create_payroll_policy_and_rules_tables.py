"""create payroll policy and rules tables

Revision ID: 89c01187645c
Revises: 8cce31ec6190
Create Date: 2025-12-02 14:44:23.008871
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "89c01187645c"
down_revision: Union[str, Sequence[str], None] = "8cce31ec6190"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "payroll_policies",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "payroll_policy_rules",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "payroll_policy_id",
            sa.Integer(),
            sa.ForeignKey("payroll_policies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule_name", sa.String(length=50), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_percentage", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("applies_to", sa.String(length=50), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("payroll_policy_rules")
    op.drop_table("payroll_policies")
