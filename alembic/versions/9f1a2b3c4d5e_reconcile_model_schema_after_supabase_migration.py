"""reconcile model schema after supabase migration

Revision ID: 9f1a2b3c4d5e
Revises: 82c026da7ef0
Create Date: 2026-05-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f1a2b3c4d5e"
down_revision: Union[str, Sequence[str], None] = "82c026da7ef0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS payroll_policies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(255),
            effective_from DATE NOT NULL,
            effective_to DATE,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
        """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_payroll_policies_id ON payroll_policies (id)")

    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS bank_name VARCHAR(50)")
    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS ifsc_code VARCHAR(11)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS attendance_overrides (
            id SERIAL PRIMARY KEY,
            employee_id VARCHAR(9) NOT NULL,
            work_date_local DATE NOT NULL,
            patch_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            note TEXT,
            acted_by VARCHAR(40) NOT NULL,
            acted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT true
        )
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_attendance_overrides_employee_id
        ON attendance_overrides (employee_id)
        """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_attendance_overrides_work_date_local
        ON attendance_overrides (work_date_local)
        """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'attendance_overrides_employee_id_fkey'
            ) THEN
                ALTER TABLE attendance_overrides
                ADD CONSTRAINT attendance_overrides_employee_id_fkey
                FOREIGN KEY (employee_id)
                REFERENCES employees(employee_id)
                ON DELETE RESTRICT
                NOT VALID;
            END IF;
        END $$;
        """)

    op.execute("""
        ALTER TABLE payroll_policy_rules
        ALTER COLUMN rule_name TYPE VARCHAR(100)
        """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'payroll_policy_rules_payroll_policy_id_fkey'
            ) THEN
                ALTER TABLE payroll_policy_rules
                ADD CONSTRAINT payroll_policy_rules_payroll_policy_id_fkey
                FOREIGN KEY (payroll_policy_id)
                REFERENCES payroll_policies(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'employee_salaries_employee_id_fkey'
            ) THEN
                ALTER TABLE employee_salaries
                ADD CONSTRAINT employee_salaries_employee_id_fkey
                FOREIGN KEY (employee_id)
                REFERENCES employees(id)
                NOT VALID;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'employee_salaries_payroll_policy_id_fkey'
            ) THEN
                ALTER TABLE employee_salaries
                ADD CONSTRAINT employee_salaries_payroll_policy_id_fkey
                FOREIGN KEY (payroll_policy_id)
                REFERENCES payroll_policies(id)
                NOT VALID;
            END IF;
        END $$;
        """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE employee_salaries
        DROP CONSTRAINT IF EXISTS employee_salaries_payroll_policy_id_fkey
        """)
    op.execute("""
        ALTER TABLE employee_salaries
        DROP CONSTRAINT IF EXISTS employee_salaries_employee_id_fkey
        """)
    op.execute("""
        ALTER TABLE payroll_policy_rules
        DROP CONSTRAINT IF EXISTS payroll_policy_rules_payroll_policy_id_fkey
        """)
    op.execute("""
        ALTER TABLE attendance_overrides
        DROP CONSTRAINT IF EXISTS attendance_overrides_employee_id_fkey
        """)
    op.execute("DROP TABLE IF EXISTS attendance_overrides")
    op.execute("ALTER TABLE employees DROP COLUMN IF EXISTS ifsc_code")
    op.execute("ALTER TABLE employees DROP COLUMN IF EXISTS bank_name")
    op.execute("DROP TABLE IF EXISTS payroll_policies")
