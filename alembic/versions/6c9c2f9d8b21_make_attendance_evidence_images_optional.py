"""make_attendance_evidence_images_optional

Revision ID: 6c9c2f9d8b21
Revises: 0525888c2c6c
Create Date: 2026-03-31 13:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c9c2f9d8b21"
down_revision: Union[str, Sequence[str], None] = "0525888c2c6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "attendance_evidences", "image_bucket", existing_type=sa.String(length=128), nullable=True
    )
    op.alter_column(
        "attendance_evidences", "image_path", existing_type=sa.String(length=255), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "attendance_evidences", "image_path", existing_type=sa.String(length=255), nullable=False
    )
    op.alter_column(
        "attendance_evidences", "image_bucket", existing_type=sa.String(length=128), nullable=False
    )
