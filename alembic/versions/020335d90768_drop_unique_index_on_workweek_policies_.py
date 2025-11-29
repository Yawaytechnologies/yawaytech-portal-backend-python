"""drop_unique_index_on_workweek_policies_region"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '020335d90768'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the unique index on region column in workweek_policies table
    op.drop_index('ix_workweek_policies_region', table_name='workweek_policies')
    # Create a non-unique index instead
    op.create_index('ix_workweek_policies_region', 'workweek_policies', ['region'])


def downgrade() -> None:
    # Drop the non-unique index
    op.drop_index('ix_workweek_policies_region', table_name='workweek_policies')
    # Recreate the unique index
    op.create_index('ix_workweek_policies_region', 'workweek_policies', ['region'], unique=True)
