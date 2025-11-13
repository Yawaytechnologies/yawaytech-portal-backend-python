"""Update leave_status_enum values to uppercase

Revision ID: c1a2b3d4e5f6
Revises: 85ede3ae26d1
Create Date: 2025-11-12 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c1a2b3d4e5f6"
down_revision = "85ede3ae26d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the existing type, create new enum type with uppercase values,
    # convert the column values by upper-casing them, then drop the old type.
    op.execute("ALTER TYPE leave_status_enum RENAME TO leave_status_enum_old;")
    op.execute(
        "CREATE TYPE leave_status_enum AS ENUM ('PENDING','APPROVED','REJECTED','CANCELLED');"
    )
    # Use upper() to map existing 'Pending' -> 'PENDING' etc
    op.execute(
        "ALTER TABLE leave_requests ALTER COLUMN status TYPE leave_status_enum USING (upper(status::text)::leave_status_enum);"
    )
    op.execute("DROP TYPE leave_status_enum_old;")


def downgrade() -> None:
    # Recreate the old Title Case enum and map values back using initcap(lower())
    op.execute(
        "CREATE TYPE leave_status_enum_old AS ENUM ('Pending','Approved','Rejected','Cancelled');"
    )
    # Map 'PENDING' -> 'Pending' etc using initcap(lower(status))
    op.execute(
        "ALTER TABLE leave_requests ALTER COLUMN status TYPE leave_status_enum_old USING (initcap(lower(status::text))::leave_status_enum_old);"
    )
    op.execute("DROP TYPE leave_status_enum;")
    op.execute("ALTER TYPE leave_status_enum_old RENAME TO leave_status_enum;")
