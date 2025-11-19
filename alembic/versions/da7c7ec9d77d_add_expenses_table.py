"""Add expenses table

Revision ID: da7c7ec9d77d
Revises: 965a0ee1feab
Create Date: 2025-11-18 12:21:51.438996
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision: str = 'da7c7ec9d77d'
down_revision: Union[str, Sequence[str], None] = '965a0ee1feab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Shared ENUM definition
expense_enum = ENUM(
    'Food', 'Transport', 'Utilities', 'Entertainment', 'Software', 'Health', 'Shopping', 'Other',
    name='expense_category',
    create_type=False  # Prevents re-creation
)

def upgrade() -> None:
    expense_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('category', expense_enum, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('added_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expenses_id'), 'expenses', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_expenses_id'), table_name='expenses')
    op.drop_table('expenses')
    expense_enum.drop(op.get_bind(), checkfirst=True)