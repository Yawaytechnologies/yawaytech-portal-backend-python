"""add_attendance_evidence_table

Revision ID: a1b2c3d4e5f7
Revises: 999999999999
Create Date: 2026-03-06 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, Sequence[str], None] = "999999999999"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create attendance_evidences table."""

    # Create enum type for evidence_type
    op.execute(
        """
        CREATE TYPE evidence_type_enum AS ENUM ('check_in', 'check_out');
        """
    )

    # Create table
    op.create_table(
        "attendance_evidences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column(
            "evidence_type",
            postgresql.ENUM("check_in", "check_out", name="evidence_type_enum"),
            nullable=False,
        ),
        sa.Column("image_bucket", sa.String(128), nullable=False),
        sa.Column("image_path", sa.String(), nullable=False),
        sa.Column("image_mime", sa.String(64), nullable=True),
        sa.Column("image_size", sa.Integer(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("verification_notes", sa.String(), nullable=True),
        sa.Column(
            "verified_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["attendance_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        "ix_evidence_session_type",
        "attendance_evidences",
        ["session_id", "evidence_type"],
    )
    op.create_index(
        "ix_evidence_verified",
        "attendance_evidences",
        ["verified"],
    )


def downgrade() -> None:
    """Downgrade schema - drop attendance_evidences table."""

    # Drop indexes
    op.drop_index("ix_evidence_verified", table_name="attendance_evidences")
    op.drop_index("ix_evidence_session_type", table_name="attendance_evidences")

    # Drop table
    op.drop_table("attendance_evidences")

    # Drop enum
    op.execute("DROP TYPE IF EXISTS evidence_type_enum;")
