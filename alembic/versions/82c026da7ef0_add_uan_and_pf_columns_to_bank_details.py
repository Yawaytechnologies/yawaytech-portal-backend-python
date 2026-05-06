"""add uan and pf columns to bank_details

Revision ID: 82c026da7ef0
Revises: 3ff64083bf16
Create Date: 2026-04-07 14:27:26.387473

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "82c026da7ef0"
down_revision: Union[str, Sequence[str], None] = "3ff64083bf16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "employee_bank_details", sa.Column("uan_number", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "employee_bank_details", sa.Column("pf_number", sa.String(length=50), nullable=True)
    )


def downgrade():
    op.drop_column("employee_bank_details", "uan_number")
    op.drop_column("employee_bank_details", "pf_number")
