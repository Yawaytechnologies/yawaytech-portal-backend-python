"""create employee_profiles

Revision ID: b38b97072083
Revises: a137758fc858
Create Date: 2026-03-05 12:10:39.820415

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b38b97072083"
down_revision: Union[str, Sequence[str], None] = "a137758fc858"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "employee_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        # FK to employees.employee_id
        sa.Column(
            "employee_id",
            sa.String(length=32),
            sa.ForeignKey("employees.employee_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("employee_code", sa.String(length=32), nullable=True),
        sa.Column("profile_bucket", sa.String(length=128), nullable=True),
        sa.Column("profile_path", sa.Text, nullable=True),
        sa.Column("profile_mime", sa.String(length=64), nullable=True),
        sa.Column("profile_size", sa.Integer, nullable=True),
        sa.Column("profile_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_employee_profiles_employee_id",
        "employee_profiles",
        ["employee_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_employee_profiles_employee_id", table_name="employee_profiles")
    op.drop_table("employee_profiles")
