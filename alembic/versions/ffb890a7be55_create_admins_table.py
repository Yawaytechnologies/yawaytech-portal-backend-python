"""create admins table

Revision ID: ffb890a7be55
Revises: 8e21d627e687
Create Date: 2025-11-18 10:57:31.586327
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "ffb890a7be55"
down_revision: Union[str, Sequence[str], None] = "8e21d627e687"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("admin_id", sa.String(length=80), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=text("true")),
        sa.Column("is_super_admin", sa.Boolean(), nullable=False, server_default=text("true")),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("admins")
