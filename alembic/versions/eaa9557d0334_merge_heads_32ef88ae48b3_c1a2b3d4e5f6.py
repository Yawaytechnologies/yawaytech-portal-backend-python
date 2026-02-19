"""merge heads 32ef88ae48b3 c1a2b3d4e5f6

Revision ID: eaa9557d0334
Revises: 32ef88ae48b3, c1a2b3d4e5f6
Create Date: 2025-11-12 18:14:18.705519

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "eaa9557d0334"
down_revision: Union[str, Sequence[str], None] = ("32ef88ae48b3", "c1a2b3d4e5f6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
