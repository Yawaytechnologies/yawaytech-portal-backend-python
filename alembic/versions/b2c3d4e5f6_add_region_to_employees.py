"""Add region to employees table

Revision ID: b2c3d4e5f6
Revises: a1b2c3d4e5f6
Create Date: 2025-11-28 16:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "employees",
        sa.Column("region", sa.String(length=8), nullable=True)
    )
    op.create_index(op.f("ix_employees_region"), "employees", ["region"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_employees_region"), table_name="employees")
    op.drop_column("employees", "region")
