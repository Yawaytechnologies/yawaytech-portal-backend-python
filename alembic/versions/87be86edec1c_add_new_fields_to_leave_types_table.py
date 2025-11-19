"""add new fields to leave_types table

Revision ID: 87be86edec1c
Revises: da7c7ec9d77d
Create Date: 2025-11-19 13:26:31.804968
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '87be86edec1c'
down_revision: Union[str, Sequence[str], None] = 'da7c7ec9d77d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('leave_types', sa.Column(
        'duration_days',
        sa.Integer(),
        nullable=False,
        server_default='0'
    ))
    op.add_column('leave_types', sa.Column(
        'monthly_limit',
        sa.Integer(),
        nullable=False,
        server_default='0'
    ))
    op.add_column('leave_types', sa.Column(
        'yearly_limit',
        sa.Integer(),
        nullable=False,
        server_default='0'
    ))
    op.add_column('leave_types', sa.Column(
        'carry_forward_allowed',
        sa.Boolean(),
        nullable=False,
        server_default=sa.text('false')
    ))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('leave_types', 'carry_forward_allowed')
    op.drop_column('leave_types', 'yearly_limit')
    op.drop_column('leave_types', 'monthly_limit')
    op.drop_column('leave_types', 'duration_days')