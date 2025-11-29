"""merge heads for monthly summary"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b3310ae3ff6b"
down_revision: Union[str, Sequence[str], None] = ("020335d90768", "70f32e7b51db")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_index("ix_workweek_policies_region", table_name="workweek_policies")

def downgrade():
    op.create_index("ix_workweek_policies_region", "workweek_policies", ["region"], unique=True)
