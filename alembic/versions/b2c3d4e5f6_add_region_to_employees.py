"""Add region to employees table

Revision ID: b2c3d4e5f6
Revises: a1b2c3d4e5f6
Create Date: 2025-11-28 16:00:00.000000
"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS region VARCHAR(8)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_employees_region ON employees (region)")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_employees_region"), table_name="employees")
    op.drop_column("employees", "region")
