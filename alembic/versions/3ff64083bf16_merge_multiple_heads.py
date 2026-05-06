"""merge multiple heads

Revision ID: 3ff64083bf16
Revises: 00e866ef6dab, 6906856c4dde
Create Date: 2026-04-02 15:28:26.203183

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "3ff64083bf16"
down_revision: Union[str, Sequence[str], None] = ("00e866ef6dab", "6906856c4dde")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
