"""Create worklogs table

Revision ID: aaf1b0408214
Revises: 87be86edec1c
Create Date: 2025-11-19 16:57:23.234606
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'aaf1b0408214'
down_revision: Union[str, Sequence[str], None] = '87be86edec1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema by creating the worklogs table."""
    op.create_table(
        'worklogs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('work_date', sa.Date, nullable=False),
        sa.Column('task', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('start_time', sa.Time, nullable=True),
        sa.Column('end_time', sa.Time, nullable=True),
        sa.Column('duration_hours', sa.Float, nullable=True),
        sa.Column('work_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )

def downgrade() -> None:
    """Downgrade schema by dropping the worklogs table."""
    op.drop_table('worklogs')