"""Update expense_category enum and expenses table

Revision ID: 2ebfc42c7973
Revises: 7d9c5ce98231
Create Date: 2025-11-20 11:13:28.214540
"""

from typing import Sequence, Union
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2ebfc42c7973"
down_revision: Union[str, Sequence[str], None] = "7d9c5ce98231"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define new and old enums
new_enum = postgresql.ENUM(
    "Food",
    "Transport",
    "Utilities",
    "Entertainment",
    "Software",
    "Health",
    "Shopping",
    "Other",
    name="expense_category",
    create_type=False,
)

old_enum = postgresql.ENUM(
    "food", "transport", "utilities", name="expense_category", create_type=False
)


def upgrade() -> None:
    # Rename old enum type
    op.execute("ALTER TYPE expense_category RENAME TO expense_category_old")

    # Create new enum type
    new_enum.create(op.get_bind())

    # Alter column to use new enum
    op.execute("""
        ALTER TABLE expenses
        ALTER COLUMN category TYPE expense_category
        USING category::text::expense_category
    """)

    # Drop old enum
    op.execute("DROP TYPE expense_category_old")


def downgrade() -> None:
    # Recreate old enum
    old_enum.create(op.get_bind())

    # Revert column to old enum
    op.execute("""
        ALTER TABLE expenses
        ALTER COLUMN category TYPE expense_category
        USING category::text::expense_category
    """)

    # Drop new enum
    op.execute("DROP TYPE expense_category")

    # Rename old enum back
    op.execute("ALTER TYPE expense_category_old RENAME TO expense_category")
