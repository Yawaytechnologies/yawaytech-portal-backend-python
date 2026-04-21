"""rename is_night to shift and convert to enum

Revision ID: 00e866ef6dab
Revises: 6c9c2f9d8b21
Create Date: 2026-04-02 12:53:36.766708

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "00e866ef6dab"
down_revision: Union[str, Sequence[str], None] = "6c9c2f9d8b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Create ENUM type
    shift_enum = sa.Enum("Day", "Afternoon", "Night", name="shift_enum")
    shift_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add new column
    op.add_column("shifts", sa.Column("shift", shift_enum, nullable=True))

    # 3. Convert old data (boolean → enum)
    op.execute(
        """
        UPDATE shifts
        SET shift =
            CASE
                WHEN is_night = true THEN 'Night'
                ELSE 'Day'
            END
    """
    )

    # 4. Make column NOT NULL (optional)
    op.alter_column("shifts", "shift", nullable=False)

    # 5. Drop old column
    op.drop_column("shifts", "is_night")


def downgrade():
    # Reverse

    # 1. Add old column back
    op.add_column("shifts", sa.Column("is_night", sa.Boolean(), nullable=True))

    # 2. Convert enum → boolean
    """rename is_night to shift and convert to enum

Revision ID: 00e866ef6dab
Revises: 6c9c2f9d8b21
Create Date: 2026-04-02 12:53:36.766708
"""


from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = "00e866ef6dab"
down_revision: Union[str, Sequence[str], None] = "6c9c2f9d8b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    shift_enum = sa.Enum("Day", "Afternoon", "Night", name="shift_enum")
    shift_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("shifts", sa.Column("shift", shift_enum, nullable=True))

    op.execute(
        """
        UPDATE shifts
        SET shift =
            CASE
                WHEN is_night = true THEN 'Night'::shift_enum
                ELSE 'Day'::shift_enum
            END
    """
    )

    op.alter_column("shifts", "shift", nullable=False)
    op.drop_column("shifts", "is_night")


def downgrade() -> None:
    op.add_column("shifts", sa.Column("is_night", sa.Boolean(), nullable=True))

    op.execute(
        """
        UPDATE shifts
        SET is_night =
            CASE
                WHEN shift = 'Night'::shift_enum THEN true
                ELSE false
            END
    """
    )

    op.alter_column("shifts", "is_night", nullable=False)
    op.drop_column("shifts", "shift")

    shift_enum = sa.Enum("Day", "Afternoon", "Night", name="shift_enum")
    shift_enum.drop(op.get_bind(), checkfirst=True)
