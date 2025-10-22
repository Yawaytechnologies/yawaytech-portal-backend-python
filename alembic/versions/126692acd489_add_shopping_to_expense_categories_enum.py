"""add_shopping_to_expense_categories_enum

Revision ID: 126692acd489
Revises: 85ede3ae26d1
Create Date: 2025-10-17 13:22:19.042471

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "126692acd489"
down_revision: Union[str, Sequence[str], None] = "85ede3ae26d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new enum value to expense_category enum
    op.execute("ALTER TYPE expense_category ADD VALUE IF NOT EXISTS 'Shopping'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL does not support removing enum values directly
    # This would require recreating the enum without the values
    # For simplicity, we'll leave the enum as is for downgrade
    pass
