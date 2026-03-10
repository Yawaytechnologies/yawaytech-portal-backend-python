"""update expense category enum to uppercase

Revision ID: 70f32e7b51db
Revises: 2ebfc42c7973
Create Date: 2025-11-20 12:00:00.000000
"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "70f32e7b51db"
down_revision: Union[str, Sequence[str], None] = "2ebfc42c7973"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE expense_category RENAME VALUE 'Food' TO 'FOOD'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'Transport' TO 'TRANSPORT'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'Utilities' TO 'UTILITIES'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'Entertainment' TO 'ENTERTAINMENT'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'Software' TO 'SOFTWARE'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'Health' TO 'HEALTH'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'Shopping' TO 'SHOPPING'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'Other' TO 'OTHER'")


def downgrade() -> None:
    op.execute("ALTER TYPE expense_category RENAME VALUE 'FOOD' TO 'Food'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'TRANSPORT' TO 'Transport'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'UTILITIES' TO 'Utilities'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'ENTERTAINMENT' TO 'Entertainment'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'SOFTWARE' TO 'Software'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'HEALTH' TO 'Health'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'SHOPPING' TO 'Shopping'")
    op.execute("ALTER TYPE expense_category RENAME VALUE 'OTHER' TO 'Other'")