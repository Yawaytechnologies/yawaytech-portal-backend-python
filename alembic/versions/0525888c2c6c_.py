"""empty message

Revision ID: 0525888c2c6c
Revises: a1b2c3d4e5f7, b38b97072083
Create Date: 2026-03-06 13:11:39.611824

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "0525888c2c6c"
down_revision: Union[str, Sequence[str], None] = ("a1b2c3d4e5f7", "b38b97072083")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
