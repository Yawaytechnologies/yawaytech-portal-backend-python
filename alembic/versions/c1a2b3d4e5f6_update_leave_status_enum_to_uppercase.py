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
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leave_status_enum')
               AND NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leave_status_enum_old') THEN
                ALTER TYPE leave_status_enum RENAME TO leave_status_enum_old;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leave_status_enum') THEN
                CREATE TYPE leave_status_enum AS ENUM (
                    'PENDING',
                    'APPROVED',
                    'REJECTED',
                    'CANCELLED'
                );
            END IF;
        END $$;
        """)

    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('public.leave_requests') IS NOT NULL
               AND EXISTS (
                   SELECT 1
                   FROM information_schema.columns
                   WHERE table_schema = 'public'
                     AND table_name = 'leave_requests'
                     AND column_name = 'status'
               ) THEN
                ALTER TABLE leave_requests
                ALTER COLUMN status TYPE leave_status_enum
                USING (upper(status::text)::leave_status_enum);
            END IF;

            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leave_status_enum_old') THEN
                DROP TYPE leave_status_enum_old;
            END IF;
        END $$;
        """)


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
