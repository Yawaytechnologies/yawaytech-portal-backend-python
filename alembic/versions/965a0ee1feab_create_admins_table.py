"""create admins table

Revision ID: 965a0ee1feab
Revises: ffb890a7be55
Create Date: 2025-11-18 11:28:17.595451
"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "965a0ee1feab"
down_revision: Union[str, Sequence[str], None] = "ffb890a7be55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            admin_id VARCHAR(80) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            is_super_admin BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.drop_table("admins")
