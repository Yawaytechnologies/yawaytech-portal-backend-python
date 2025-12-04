"""Add employee_salary, salary_breakdown, employee_bank_detail

Revision ID: a137758fc858
Revises: 3677d45bc469
Create Date: 2025-12-04 12:20:00.707551
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a137758fc858"
down_revision: Union[str, Sequence[str], None] = "3677d45bc469"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Employee Salary table
    op.create_table(
        "employee_salaries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employee_id", sa.Integer, nullable=False),
        sa.Column("base_salary", sa.Float, nullable=False),
        sa.Column("gross_salary", sa.Float, nullable=False),
        sa.Column("payroll_policy_id", sa.Integer, sa.ForeignKey("payroll_policies.id")),
    )

    # Salary Breakdown table - use raw SQL to avoid enum creation issue
    op.execute(
        """
        CREATE TABLE salary_breakdowns (
            id SERIAL PRIMARY KEY,
            employee_salary_id INTEGER NOT NULL REFERENCES employee_salaries(id),
            rule_name VARCHAR(100) NOT NULL,
            rule_type rule_type_enum NOT NULL,
            applies_to VARCHAR(50) NOT NULL,
            amount FLOAT NOT NULL
        )
    """
    )

    # Employee Bank Detail table
    op.create_table(
        "employee_bank_details",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("bank_name", sa.String(100), nullable=False),
        sa.Column("account_number", sa.String(50), nullable=False),
        sa.Column("ifsc_code", sa.String(20), nullable=False),
        sa.Column("branch_name", sa.String(100)),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("employee_bank_details")
    op.drop_table("salary_breakdowns")
    op.drop_table("employee_salaries")
