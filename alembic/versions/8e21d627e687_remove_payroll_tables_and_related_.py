"""Remove payroll tables and related columns

Revision ID: 8e21d627e687
Revises: 641108578efe
Create Date: 2025-11-17 17:33:55.816661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e21d627e687'
down_revision: Union[str, Sequence[str], None] = '641108578efe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop payroll tables
    op.drop_table('payroll_items')
    op.drop_table('payroll_runs')
    op.drop_table('pay_periods')
    op.drop_table('employee_salary')

    # Drop payroll-related columns from employees table
    op.drop_column('employees', 'bank_name')
    op.drop_column('employees', 'ifsc_code')

    # Drop payroll-related columns from employee_salary table (already dropped above)
    # Note: employee_salary table is dropped, so no need to drop columns


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate payroll-related columns in employees table
    op.add_column('employees', sa.Column('bank_name', sa.String(), nullable=True))
    op.add_column('employees', sa.Column('ifsc_code', sa.String(), nullable=True))

    # Recreate employee_salary table
    op.create_table('employee_salary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('basic_salary', sa.Float(), nullable=False),
        sa.Column('pf_scheme', sa.String(), nullable=True),
        sa.Column('esi_scheme', sa.String(), nullable=True),
        sa.Column('gratuity_scheme', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Recreate pay_periods table
    op.create_table('pay_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Recreate payroll_runs table
    op.create_table('payroll_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pay_period_id', sa.Integer(), nullable=False),
        sa.Column('run_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pay_period_id'], ['pay_periods.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Recreate payroll_items table
    op.create_table('payroll_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payroll_run_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('basic_salary', sa.Float(), nullable=False),
        sa.Column('allowances', sa.Float(), nullable=True),
        sa.Column('deductions', sa.Float(), nullable=True),
        sa.Column('net_salary', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['payroll_run_id'], ['payroll_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
