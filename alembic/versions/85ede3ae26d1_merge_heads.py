"""Merge heads

Revision ID: 85ede3ae26d1
Revises: 6bce6867c6cb, abc3a337ad9f
Create Date: 2025-10-17 11:03:53.815433

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "85ede3ae26d1"
down_revision: Union[str, Sequence[str], None] = ("6bce6867c6cb", "abc3a337ad9f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
