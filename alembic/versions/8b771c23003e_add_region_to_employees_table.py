"""add region to employees table

Revision ID: 8b771c23003e
Revises: a1b2c3d4e5f6
Create Date: 2025-11-28 12:58:37.281084
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8b771c23003e"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add region column to employees
    op.add_column("employees", sa.Column("region", sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove region column from employees
    op.drop_column("employees", "region")
