"""change_start_end_time_to_time_only

Revision ID: abc3a337ad9f
Revises: 0ff9a4ab8a6a
Create Date: 2025-10-16 10:30:01.402322

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "abc3a337ad9f"
down_revision: Union[str, Sequence[str], None] = "0ff9a4ab8a6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change start_time and end_time from TIMESTAMP to TIME
    op.alter_column("worklogs", "start_time", type_=sa.Time(), existing_nullable=True)
    op.alter_column("worklogs", "end_time", type_=sa.Time(), existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Change start_time and end_time back to TIMESTAMP
    op.alter_column("worklogs", "start_time", type_=sa.DateTime(), existing_nullable=True)
    op.alter_column("worklogs", "end_time", type_=sa.DateTime(), existing_nullable=True)
