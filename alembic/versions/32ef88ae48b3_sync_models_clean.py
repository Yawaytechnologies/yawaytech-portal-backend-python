"""sync models (clean)

Revision ID: 32ef88ae48b3
Revises: 4be08f0f866c
Create Date: 2025-11-06 17:17:35.010135
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "32ef88ae48b3"
down_revision: Union[str, Sequence[str], None] = "4be08f0f866c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_not_null_int(table: str, col: str, default: int):
    # 1) add as NULLable
    op.add_column(table, sa.Column(col, sa.Integer(), nullable=True))
    # 2) backfill
    op.execute(f"UPDATE {table} SET {col} = {default} WHERE {col} IS NULL")
    # 3) enforce NOT NULL
    op.alter_column(table, col, existing_type=sa.Integer(), nullable=False)


def upgrade() -> None:
    """Upgrade schema."""
    # ───────────────── new core tables ─────────────────
    op.create_table(
        "holiday_calendar",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("holiday_date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("is_paid", sa.Boolean(), nullable=False),
        sa.Column("region", sa.String(length=8), nullable=True),
        sa.Column("recurs_annually", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_holiday_calendar_holiday_date"),
        "holiday_calendar",
        ["holiday_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_holiday_calendar_region"), "holiday_calendar", ["region"], unique=False
    )
    op.create_index(
        "ix_holiday_region_date",
        "holiday_calendar",
        ["region", "holiday_date"],
        unique=False,
    )

    op.create_table(
        "leave_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("unit", sa.Enum("DAY", "HOUR", name="leave_unit_enum"), nullable=False),
        sa.Column("is_paid", sa.Boolean(), nullable=False),
        sa.Column("allow_half_day", sa.Boolean(), nullable=False),
        sa.Column("allow_permission_hours", sa.Boolean(), nullable=False),
        sa.CheckConstraint("code ~ '^[A-Z]{2,16}$'", name="ck_leave_type_code"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_leave_types_code"), "leave_types", ["code"], unique=True)

    op.create_table(
        "pay_periods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=7), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("start_date <= end_date", name="ck_period_range"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pay_periods_code"), "pay_periods", ["code"], unique=True)

    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=30), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("total_hours", sa.Integer(), nullable=False),
        sa.Column("is_night", sa.Boolean(), nullable=False),
        sa.CheckConstraint("total_hours BETWEEN 1 AND 24", name="ck_shift_total_hours"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shifts_name"), "shifts", ["name"], unique=True)

    op.create_table(
        "workweek_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(length=8), nullable=False),
        sa.Column(
            "policy_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_workweek_policies_region"),
        "workweek_policies",
        ["region"],
        unique=True,
    )

    op.create_table(
        "employee_salary",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.String(length=9), nullable=False),
        sa.Column("salary_type", sa.String(length=8), nullable=False),
        sa.Column("base_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("salary_type IN ('MONTHLY','HOURLY')", name="ck_emp_salary_type"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_emp_salary_emp_from",
        "employee_salary",
        ["employee_id", "effective_from"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_salary_effective_from"),
        "employee_salary",
        ["effective_from"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_salary_employee_id"),
        "employee_salary",
        ["employee_id"],
        unique=False,
    )

    op.create_table(
        "employee_shift_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.String(length=9), nullable=False),
        sa.Column("shift_id", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "(effective_to IS NULL) OR (effective_to >= effective_from)",
            name="ck_shift_assign_range",
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employee_id", "shift_id", "effective_from", name="uq_shift_assign_start"
        ),
    )
    op.create_index(
        op.f("ix_employee_shift_assignments_effective_from"),
        "employee_shift_assignments",
        ["effective_from"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_shift_assignments_employee_id"),
        "employee_shift_assignments",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        "ix_shift_assign_emp_from",
        "employee_shift_assignments",
        ["employee_id", "effective_from"],
        unique=False,
    )

    op.create_table(
        "leave_balances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.String(length=9), nullable=False),
        sa.Column("leave_type_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("opening", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("accrued", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("used", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("adjusted", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("closing", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.CheckConstraint("year BETWEEN 1970 AND 2100", name="ck_leave_balance_year"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["leave_type_id"], ["leave_types.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employee_id",
            "leave_type_id",
            "year",
            name="uq_leave_balance_emp_type_year",
        ),
    )
    op.create_index(
        "ix_leave_balance_emp_year",
        "leave_balances",
        ["employee_id", "year"],
        unique=False,
    )
    op.create_index(
        op.f("ix_leave_balances_employee_id"),
        "leave_balances",
        ["employee_id"],
        unique=False,
    )

    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.String(length=9), nullable=False),
        sa.Column("leave_type_id", sa.Integer(), nullable=False),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "requested_unit",
            sa.Enum("DAY", "HALF_DAY", "HOUR", name="leave_req_unit_enum"),
            nullable=False,
        ),
        sa.Column("requested_hours", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "APPROVED", "REJECTED", "CANCELLED", name="leave_status_enum"),
            nullable=False,
        ),
        sa.Column("approver_employee_id", sa.String(length=9), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("end_datetime >= start_datetime", name="ck_leave_req_range"),
        sa.ForeignKeyConstraint(["approver_employee_id"], ["employees.employee_id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["leave_type_id"], ["leave_types.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_leave_requests_employee_id"),
        "leave_requests",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_leave_requests_end_datetime"),
        "leave_requests",
        ["end_datetime"],
        unique=False,
    )
    op.create_index(
        op.f("ix_leave_requests_start_datetime"),
        "leave_requests",
        ["start_datetime"],
        unique=False,
    )

    op.create_table(
        "payroll_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pay_period_id", sa.Integer(), nullable=False),
        sa.Column("run_no", sa.Integer(), nullable=False),
        sa.Column("run_status", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("run_status IN ('Draft','Finalized')", name="ck_run_status"),
        sa.ForeignKeyConstraint(["pay_period_id"], ["pay_periods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pay_period_id", "run_no", name="uq_payroll_run_period_no"),
    )
    op.create_index(
        op.f("ix_payroll_runs_pay_period_id"),
        "payroll_runs",
        ["pay_period_id"],
        unique=False,
    )

    op.create_table(
        "payroll_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payroll_run_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.String(length=9), nullable=False),
        sa.Column("salary_type", sa.String(length=8), nullable=False),
        sa.Column("base_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("standard_workdays", sa.Integer(), nullable=False),
        sa.Column("per_day_rate", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("per_hour_rate", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("ot_multiplier", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("paid_days", sa.Integer(), nullable=False),
        sa.Column("unpaid_days", sa.Integer(), nullable=False),
        sa.Column("underwork_hours", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("overtime_hours", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("gross_earnings", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_deductions", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("net_pay", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "breakdown_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("gross_earnings >= 0", name="ck_payroll_items_gross_nonneg"),
        sa.CheckConstraint("net_pay >= 0", name="ck_payroll_items_net_nonneg"),
        sa.CheckConstraint("total_deductions >= 0", name="ck_payroll_items_ded_nonneg"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payroll_run_id"], ["payroll_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payroll_run_id", "employee_id", name="uq_payroll_items_run_emp"),
    )
    op.create_index(
        op.f("ix_payroll_items_employee_id"),
        "payroll_items",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payroll_items_payroll_run_id"),
        "payroll_items",
        ["payroll_run_id"],
        unique=False,
    )

    # ───────────────── modify attendance tables safely ─────────────────
    # expected_seconds (8h default)
    op.add_column("attendance_days", sa.Column("expected_seconds", sa.Integer(), nullable=True))
    op.execute("UPDATE attendance_days SET expected_seconds = 28800 WHERE expected_seconds IS NULL")
    op.alter_column(
        "attendance_days",
        "expected_seconds",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # metrics → default 0
    _add_not_null_int("attendance_days", "paid_leave_seconds", 0)
    _add_not_null_int("attendance_days", "overtime_seconds", 0)
    _add_not_null_int("attendance_days", "underwork_seconds", 0)
    _add_not_null_int("attendance_days", "unpaid_seconds", 0)

    # leave_type_code (nullable) already fine in autogen above if needed
    op.add_column(
        "attendance_days",
        sa.Column("leave_type_code", sa.String(length=16), nullable=True),
    )

    # lock_flag boolean → default false
    op.add_column("attendance_days", sa.Column("lock_flag", sa.Boolean(), nullable=True))
    op.execute("UPDATE attendance_days SET lock_flag = FALSE WHERE lock_flag IS NULL")
    op.alter_column("attendance_days", "lock_flag", existing_type=sa.Boolean(), nullable=False)

    # created_at / updated_at with server default now()
    op.add_column(
        "attendance_days",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "attendance_days",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # status → normalize & convert to ENUM with Title-Case labels
    # Normalize existing data to match enum labels exactly
    op.execute("""
        UPDATE attendance_days
        SET status = CASE UPPER(status)
            WHEN 'PRESENT' THEN 'Present'
            WHEN 'ABSENT'  THEN 'Absent'
            WHEN 'LEAVE'   THEN 'Leave'
            WHEN 'HOLIDAY' THEN 'Holiday'
            WHEN 'WEEKEND' THEN 'Weekend'
            ELSE 'Present'
        END
        """)
    day_status_enum = sa.Enum(
        "Present", "Absent", "Leave", "Holiday", "Weekend", name="day_status_enum"
    )
    day_status_enum.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        "attendance_days",
        "status",
        existing_type=sa.VARCHAR(length=20),
        type_=day_status_enum,
        existing_nullable=False,
        postgresql_using="status::text::day_status_enum",
    )

    # rename unique constraint to your new name
    op.drop_constraint(op.f("uq_attendance_day"), "attendance_days", type_="unique")
    op.create_unique_constraint(
        "uq_attendance_day_emp_date",
        "attendance_days",
        ["employee_id", "work_date_local"],
    )

    # attendance_sessions timestamps + helpful index
    op.add_column(
        "attendance_sessions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "attendance_sessions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_session_emp_date",
        "attendance_sessions",
        ["employee_id", "work_date_local"],
        unique=False,
    )

    # checkin_monitoring JSON → JSONB (with [] default)
    op.alter_column(
        "checkin_monitoring",
        "active_apps",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        server_default="[]",
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
    )
    op.alter_column(
        "checkin_monitoring",
        "visited_sites",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        server_default="[]",
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
    )

    # employees PAN/AADHAAR indexes + uniques (keep if you want both)
    op.create_index(op.f("ix_employees_aadhar_number"), "employees", ["aadhar_number"], unique=True)
    op.create_index(op.f("ix_employees_pan_number"), "employees", ["pan_number"], unique=True)
    op.create_unique_constraint("uq_employee_aadhar_number", "employees", ["aadhar_number"])
    op.create_unique_constraint("uq_employee_pan_number", "employees", ["pan_number"])


def downgrade() -> None:
    """Downgrade schema (best-effort)."""
    # employees
    op.drop_constraint("uq_employee_pan_number", "employees", type_="unique")
    op.drop_constraint("uq_employee_aadhar_number", "employees", type_="unique")
    op.drop_index(op.f("ix_employees_pan_number"), table_name="employees")
    op.drop_index(op.f("ix_employees_aadhar_number"), table_name="employees")

    # checkin_monitoring JSONB → JSON
    op.alter_column(
        "checkin_monitoring",
        "visited_sites",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        server_default=None,
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_nullable=False,
    )
    op.alter_column(
        "checkin_monitoring",
        "active_apps",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        server_default=None,
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_nullable=False,
    )

    # attendance_sessions
    op.drop_index("ix_session_emp_date", table_name="attendance_sessions")
    op.drop_column("attendance_sessions", "updated_at")
    op.drop_column("attendance_sessions", "created_at")

    # attendance_days – revert enum to varchar then drop added cols
    day_status_enum = sa.Enum(
        "Present", "Absent", "Leave", "Holiday", "Weekend", name="day_status_enum"
    )
    op.alter_column(
        "attendance_days",
        "status",
        existing_type=day_status_enum,
        type_=sa.VARCHAR(length=20),
        existing_nullable=False,
        postgresql_using="status::text",
    )
    day_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_constraint("uq_attendance_day_emp_date", "attendance_days", type_="unique")
    op.create_unique_constraint(
        op.f("uq_attendance_day"), "attendance_days", ["employee_id", "work_date_local"]
    )

    for col in (
        "updated_at",
        "created_at",
        "lock_flag",
        "leave_type_code",
        "unpaid_seconds",
        "underwork_seconds",
        "overtime_seconds",
        "paid_leave_seconds",
        "expected_seconds",
    ):
        op.drop_column("attendance_days", col)

    # payroll tables
    op.drop_index(op.f("ix_payroll_items_payroll_run_id"), table_name="payroll_items")
    op.drop_index(op.f("ix_payroll_items_employee_id"), table_name="payroll_items")
    op.drop_table("payroll_items")

    op.drop_index(op.f("ix_payroll_runs_pay_period_id"), table_name="payroll_runs")
    op.drop_table("payroll_runs")

    # leave requests/balances
    op.drop_index(op.f("ix_leave_requests_start_datetime"), table_name="leave_requests")
    op.drop_index(op.f("ix_leave_requests_end_datetime"), table_name="leave_requests")
    op.drop_index(op.f("ix_leave_requests_employee_id"), table_name="leave_requests")
    op.drop_table("leave_requests")

    op.drop_index(op.f("ix_leave_balances_employee_id"), table_name="leave_balances")
    op.drop_index("ix_leave_balance_emp_year", table_name="leave_balances")
    op.drop_table("leave_balances")

    # shifts / assignments
    op.drop_index("ix_shift_assign_emp_from", table_name="employee_shift_assignments")
    op.drop_index(
        op.f("ix_employee_shift_assignments_employee_id"),
        table_name="employee_shift_assignments",
    )
    op.drop_index(
        op.f("ix_employee_shift_assignments_effective_from"),
        table_name="employee_shift_assignments",
    )
    op.drop_table("employee_shift_assignments")

    op.drop_index(op.f("ix_employee_salary_employee_id"), table_name="employee_salary")
    op.drop_index(op.f("ix_employee_salary_effective_from"), table_name="employee_salary")
    op.drop_index("ix_emp_salary_emp_from", table_name="employee_salary")
    op.drop_table("employee_salary")

    op.drop_index(op.f("ix_workweek_policies_region"), table_name="workweek_policies")
    op.drop_table("workweek_policies")

    op.drop_index(op.f("ix_shifts_name"), table_name="shifts")
    op.drop_table("shifts")

    op.drop_index(op.f("ix_pay_periods_code"), table_name="pay_periods")
    op.drop_table("pay_periods")

    op.drop_index(op.f("ix_leave_types_code"), table_name="leave_types")
    op.drop_table("leave_types")

    op.drop_index("ix_holiday_region_date", table_name="holiday_calendar")
    op.drop_index(op.f("ix_holiday_calendar_region"), table_name="holiday_calendar")
    op.drop_index(op.f("ix_holiday_calendar_holiday_date"), table_name="holiday_calendar")
    op.drop_table("holiday_calendar")
