"""Add worklog table

Revision ID: a05ef679ed18
Revises: c778e18d2711
Create Date: 2025-10-03 17:45:20.486603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a05ef679ed18'
down_revision: Union[str, Sequence[str], None] = 'c778e18d2711'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create worklogs table
    op.create_table('worklogs',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.VARCHAR(length=50), nullable=False),
        sa.Column('work_date', sa.DATE(), nullable=True),
        sa.Column('task', sa.VARCHAR(length=100), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=False),
        sa.Column('start_time', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('end_time', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('duration_hours', sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column('work_type', postgresql.ENUM('FEATURE', 'BUG_FIX', 'MEETING', 'TRAINING', 'SUPPORT', 'OTHER', name='worktype'), nullable=True),
        sa.Column('status', postgresql.ENUM('TODO', 'IN_PROGRESS', 'DONE', name='worklogstatus'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], name=op.f('worklogs_employee_id_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('worklogs_pkey'))
    )
    op.create_index(op.f('ix_worklogs_employee_id'), 'worklogs', ['employee_id'], unique=False)
    op.create_index(op.f('ix_worklogs_work_date'), 'worklogs', ['work_date'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # Drop worklogs table
    op.drop_index(op.f('ix_worklogs_work_date'), table_name='worklogs')
    op.drop_index(op.f('ix_worklogs_employee_id'), table_name='worklogs')
    op.drop_table('worklogs')
    # Drop enums if needed, but since they might be used elsewhere, leave them
    # ### end Alembic commands ###
