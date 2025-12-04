"""add rule_type enum

Revision ID: 3677d45bc469
Revises: 89c01187645c
Create Date: 2025-12-03 09:55:38.296732
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3677d45bc469"
down_revision: Union[str, Sequence[str], None] = "89c01187645c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the enum type
rule_type_enum = sa.Enum("ALLOWANCE", "DEDUCTION", name="rule_type_enum")


def upgrade() -> None:
    # Create the enum type in Postgres
    rule_type_enum.create(op.get_bind(), checkfirst=True)

    # Add the new column using that enum type
    op.add_column(
        "payroll_policy_rules",
        sa.Column(
            "rule_type",
            rule_type_enum,
            nullable=False,
            server_default="ALLOWANCE",  # temporary default for existing rows
        ),
    )

    # Remove the default after backfilling if needed
    op.alter_column("payroll_policy_rules", "rule_type", server_default=None)


def downgrade() -> None:
    # Drop the column
    op.drop_column("payroll_policy_rules", "rule_type")

    # Drop the enum type itself
    rule_type_enum.drop(op.get_bind(), checkfirst=True)
