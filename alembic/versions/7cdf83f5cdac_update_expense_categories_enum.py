"""Update expense categories enum

Revision ID: 7cdf83f5cdac
Revises: 999999999999
Create Date: 2025-10-15 12:01:43.327206

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7cdf83f5cdac"
down_revision: Union[str, Sequence[str], None] = "999999999999"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'expense_category') THEN
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
            END IF;
        END $$;
        """
    )

    # Add new enum values to expense_category enum
    op.execute("ALTER TYPE expense_category ADD VALUE IF NOT EXISTS 'Office'")
    op.execute("ALTER TYPE expense_category ADD VALUE IF NOT EXISTS 'Travel'")
    op.execute("ALTER TYPE expense_category ADD VALUE IF NOT EXISTS 'Software'")
    op.execute("ALTER TYPE expense_category ADD VALUE IF NOT EXISTS 'Health'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
