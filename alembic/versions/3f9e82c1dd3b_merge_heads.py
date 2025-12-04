"""add region to employees table and drop attendance_sessions safely

Revision ID: 3f9e82c1dd3b
Revises: a1b2c3d4e5f6
Create Date: 2025-11-29 22:30:08.861251
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "3f9e82c1dd3b"
down_revision: Union[str, Sequence[str], None] = ["8b771c23003e", "b2c3d4e5f6"]
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
