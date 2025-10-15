"""Drop activity_log table

Revision ID: 37547802c77d
Revises: 7cdf83f5cdac
Create Date: 2025-10-15 12:21:18.432110

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "37547802c77d"
down_revision: Union[str, Sequence[str], None] = "7cdf83f5cdac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the activity_log table
    op.drop_table("activity_log")


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate the activity_log table
    op.create_table(
        "activity_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["employees.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
