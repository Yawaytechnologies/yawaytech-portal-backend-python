"""drop unique index on workweek_policies_region

Revision ID: 23a3f9bb26fd
Revises: b3310ae3ff6b
Create Date: 2025-11-26 17:43:26.250610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23a3f9bb26fd'
down_revision: Union[str, Sequence[str], None] = 'b3310ae3ff6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
