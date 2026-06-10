"""Phase 4 – Buchhaltung Teil 1: Konten, Geschäftsjahre, Budget.

Revision ID: b1f7a4c2d590
Revises: d4e8f1a2b903
Create Date: 2026-06-10

Neue Tabellen: accounts, fiscal_years, budget_entries.
Spezifikation: docs/capabilities/accounting.md Sektion 4.1 / 4.2 / 4.5.
"""

from alembic import op
import sqlalchemy as sa


revision = "b1f7a4c2d590"
down_revision = "d4e8f1a2b903"
branch_labels = None
depends_on = None


fiscal_year_status = sa.Enum("OPEN", "IN_REVIEW", "CLOSED", name="fiscalyearstatus")
account_kind = sa.Enum("INCOME", "EXPENSE", name="accountkind")


def upgrade():
    op.create_table(
        "fiscal_years",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", fiscal_year_status, nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fiscal_years_year", "fiscal_years", ["year"], unique=True)

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("kind", account_kind, nullable=False),
        sa.Column("group_name", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounts_code", "accounts", ["code"], unique=True)

    op.create_table(
        "budget_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fiscal_year_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("amount_rappen", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["fiscal_year_id"], ["fiscal_years.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fiscal_year_id", "account_id", name="uq_budget_year_account"),
    )
    op.create_index(
        "ix_budget_entries_fiscal_year_id", "budget_entries", ["fiscal_year_id"]
    )
    op.create_index("ix_budget_entries_account_id", "budget_entries", ["account_id"])


def downgrade():
    op.drop_index("ix_budget_entries_account_id", table_name="budget_entries")
    op.drop_index("ix_budget_entries_fiscal_year_id", table_name="budget_entries")
    op.drop_table("budget_entries")

    op.drop_index("ix_accounts_code", table_name="accounts")
    op.drop_table("accounts")

    op.drop_index("ix_fiscal_years_year", table_name="fiscal_years")
    op.drop_table("fiscal_years")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        fiscal_year_status.drop(bind, checkfirst=True)
        account_kind.drop(bind, checkfirst=True)
