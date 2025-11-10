from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# IDs
revision: str = "4be08f0f866c"
down_revision: Union[str, Sequence[str], None] = (
    "0f318daf3de7"  # keep your real previous rev here
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("pan_number", sa.String(10), nullable=True))
    op.add_column("employees", sa.Column("aadhar_number", sa.String(12), nullable=True))


def downgrade() -> None:
    op.drop_column("employees", "aadhar_number")
    op.drop_column("employees", "pan_number")
