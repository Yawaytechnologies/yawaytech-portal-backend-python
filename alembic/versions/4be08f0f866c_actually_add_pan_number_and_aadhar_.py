from alembic import op
from typing import Sequence, Union

# IDs
revision: str = "4be08f0f866c"
down_revision: Union[str, Sequence[str], None] = "0f318daf3de7"  # keep your real previous rev here
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS pan_number VARCHAR(10)")
    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS aadhar_number VARCHAR(12)")


def downgrade() -> None:
    op.drop_column("employees", "aadhar_number")
    op.drop_column("employees", "pan_number")
