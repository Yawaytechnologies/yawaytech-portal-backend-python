"""Create expense_category enum

Revision ID: 6bce6867c6cb
Revises: abc3a337ad9f
Create Date: 2025-10-17 10:54:14.733030

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6bce6867c6cb"
down_revision: Union[str, Sequence[str], None] = "999999999999"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the expense_category enum
    op.execute("""
        CREATE TYPE expense_category AS ENUM (
            'Food',
            'Transport',
            'Utilities',
            'Entertainment',
            'Progress',
            'Office',
            'Travel',
            'Software',
            'Health',
            'Other'
        );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the expense_category enum
    op.execute("DROP TYPE IF EXISTS expense_category;")
