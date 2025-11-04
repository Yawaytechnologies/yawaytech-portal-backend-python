"""add pan_number and aadhar_number to employees

Revision ID: 0f318daf3de7
Revises: 126692acd489
Create Date: 2025-11-03 11:19:48.154363
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0f318daf3de7"
down_revision: Union[str, Sequence[str], None] = "126692acd489"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "employees",
        sa.Column("pan_number", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "employees",
        sa.Column("aadhar_number", sa.String(length=12), nullable=True),
    )
    # Optional (safer than constraints if many NULLs exist):
    # op.create_index("ix_employees_pan_number", "employees", ["pan_number"], unique=True)
    # op.create_index("ix_employees_aadhar_number", "employees", ["aadhar_number"], unique=True)
    op.create_index(op.f("ix_aadhar_number"), "employees", ["aadhar_number"], unique=False),
    op.create_index(op.f("ix_pan_number"), "employees", ["pan"], unique=False),



def downgrade() -> None:
    """Downgrade schema."""
    # If you created indexes above, drop them first:
    # op.drop_index("ix_employees_aadhar_number", table_name="employees")
    # op.drop_index("ix_employees_pan_number", table_name="employees")
    op.drop_column("employees", "aadhar_number")
    op.drop_column("employees", "pan_number")
