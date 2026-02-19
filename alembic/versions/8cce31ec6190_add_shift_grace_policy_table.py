"""add shift_grace_policies table

Revision ID: 8cce31ec6190
Revises: 3f9e82c1dd3b
Create Date: 2025-11-29 23:00:00.000000
"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8cce31ec6190"
down_revision: Union[str, Sequence[str], None] = "3f9e82c1dd3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create enums only if they don't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'grace_type_enum') THEN
                CREATE TYPE grace_type_enum AS ENUM ('BEFORE_START', 'AFTER_END', 'BOTH');
            END IF;
        END
        $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'applies_to_enum') THEN
                CREATE TYPE applies_to_enum AS ENUM ('LATE_ARRIVAL', 'EARLY_EXIT', 'UNDERWORK');
            END IF;
        END
        $$;
    """)

    # Create shift_grace_policies table using raw SQL to avoid enum creation issues
    op.execute("""
        CREATE TABLE shift_grace_policies (
            id SERIAL PRIMARY KEY,
            shift_id INTEGER NOT NULL REFERENCES shifts(id) ON DELETE CASCADE,
            grace_type grace_type_enum NOT NULL,
            applies_to applies_to_enum NOT NULL,
            excused_minutes INTEGER NOT NULL DEFAULT 30,
            effective_from DATE NOT NULL,
            effective_to DATE,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)

    # Constraints and indexes
    op.create_check_constraint(
        "ck_grace_minutes",
        "shift_grace_policies",
        "excused_minutes BETWEEN 0 AND 120",
    )
    op.create_unique_constraint(
        "uq_grace_policy",
        "shift_grace_policies",
        ["shift_id", "applies_to", "effective_from"],
    )
    op.create_index(
        "ix_grace_policy_shift",
        "shift_grace_policies",
        ["shift_id", "effective_from"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_grace_policy_shift", table_name="shift_grace_policies")
    op.drop_constraint("uq_grace_policy", "shift_grace_policies", type_="unique")
    op.drop_constraint("ck_grace_minutes", "shift_grace_policies", type_="check")

    op.drop_table("shift_grace_policies")

    op.execute("DROP TYPE IF EXISTS applies_to_enum")
    op.execute("DROP TYPE IF EXISTS grace_type_enum")
