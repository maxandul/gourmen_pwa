"""Phase 4b – ZKB-Import, Offene Posten, BillBro-Zahlweg.

Revision ID: a4b7c2d9e015
Revises: f2c8a1b9d047
Create Date: 2026-07-13

Neue Tabellen: bank_statement_imports, bank_transactions,
member_bank_aliases, member_claims.
Erweiterungen: events.bill_paid_by + events.bill_payer_member_id,
fiscal_years.membership_fee_rappen, EventType ESSEN_BUCHHALTUNG.
Spezifikation: docs/capabilities/accounting.md Sektion 11.2.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a4b7c2d9e015"
down_revision = "f2c8a1b9d047"
branch_labels = None
depends_on = None


# sa.Enum fuer idempotentes .create() / .drop() in upgrade()/downgrade()
bank_tx_status = sa.Enum("PENDING", "BOOKED", "IGNORED", name="banktransactionstatus")
claim_type = sa.Enum(
    "MITGLIEDERBEITRAG", "ESSENSANTEIL", "MERCH", "REISE", "SONSTIGES",
    name="claimtype",
)
claim_status = sa.Enum("OFFEN", "TEILWEISE", "BEGLICHEN", "ERLASSEN", name="claimstatus")
bill_paid_by = sa.Enum("vereinskonto", "mitglied", name="billpaidby")
booking_direction = sa.Enum("IN", "OUT", name="bookingdirection")

# postgresql.ENUM + create_type=False fuer Spalten in create_table / batch_alter_table.
# In SQLAlchemy 2.0.x wird create_type nur hier beachtet, nicht bei sa.Enum – sonst
# emittiert op.create_table erneut CREATE TYPE (Retry-Kollision nach fehlgeschlagenem Deploy).
bank_tx_status_col = postgresql.ENUM(
    "PENDING", "BOOKED", "IGNORED", name="banktransactionstatus", create_type=False,
)
claim_type_col = postgresql.ENUM(
    "MITGLIEDERBEITRAG", "ESSENSANTEIL", "MERCH", "REISE", "SONSTIGES",
    name="claimtype", create_type=False,
)
claim_status_col = postgresql.ENUM(
    "OFFEN", "TEILWEISE", "BEGLICHEN", "ERLASSEN", name="claimstatus", create_type=False,
)
bill_paid_by_col = postgresql.ENUM(
    "vereinskonto", "mitglied", name="billpaidby", create_type=False,
)
booking_direction_col = postgresql.ENUM(
    "IN", "OUT", name="bookingdirection", create_type=False,
)


def upgrade():
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        # Nicht-transaktional; Muster wie f2c8a1b9d047 (VORSTANDSSITZUNG)
        op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'ESSEN_BUCHHALTUNG'")
        bank_tx_status.create(bind, checkfirst=True)
        claim_type.create(bind, checkfirst=True)
        claim_status.create(bind, checkfirst=True)
        bill_paid_by.create(bind, checkfirst=True)
        # bookingdirection: Phase-4-Migration c8d3e9f1a274 oder fehlgeschlagenes Retry
        booking_direction.create(bind, checkfirst=True)

    # --- fiscal_years: Jahresbeitrag pro Mitglied ---
    with op.batch_alter_table("fiscal_years", schema=None) as batch_op:
        batch_op.add_column(sa.Column("membership_fee_rappen", sa.Integer(), nullable=True))

    # --- events: Zahlweg ---
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("bill_paid_by", bill_paid_by_col, nullable=True))
        batch_op.add_column(sa.Column("bill_payer_member_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_events_bill_payer_member_id", "members",
            ["bill_payer_member_id"], ["id"], ondelete="SET NULL",
        )

    # --- bank_statement_imports ---
    op.create_table(
        "bank_statement_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fiscal_year_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("imported_by", sa.Integer(), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("new_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["fiscal_year_id"], ["fiscal_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["imported_by"], ["members.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bank_statement_imports_fiscal_year_id",
        "bank_statement_imports", ["fiscal_year_id"],
    )

    # --- bank_transactions ---
    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("zkb_ref", sa.String(length=50), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("line_key", sa.String(length=60), nullable=False),
        sa.Column("booked_date", sa.Date(), nullable=False),
        sa.Column("valuta", sa.Date(), nullable=True),
        sa.Column("amount_rappen", sa.Integer(), nullable=False),
        sa.Column("direction", booking_direction_col, nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("amount_original", sa.String(length=30), nullable=True),
        sa.Column("buchungstext", sa.String(length=500), nullable=False),
        sa.Column("zahlungszweck", sa.String(length=500), nullable=True),
        sa.Column("details", sa.String(length=500), nullable=True),
        sa.Column("status", bank_tx_status_col, nullable=False, server_default="PENDING"),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("suggested_account_id", sa.Integer(), nullable=True),
        sa.Column("suggested_member_id", sa.Integer(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["import_id"], ["bank_statement_imports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["bank_transactions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["suggested_account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["suggested_member_id"], ["members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("line_key", name="uq_bank_transactions_line_key"),
    )
    op.create_index("ix_bank_transactions_import_id", "bank_transactions", ["import_id"])
    op.create_index("ix_bank_transactions_zkb_ref", "bank_transactions", ["zkb_ref"])
    op.create_index("ix_bank_transactions_parent_id", "bank_transactions", ["parent_id"])
    op.create_index("ix_bank_transactions_line_key", "bank_transactions", ["line_key"])
    op.create_index("ix_bank_transactions_status", "bank_transactions", ["status"])
    op.create_index("ix_bank_transactions_booking_id", "bank_transactions", ["booking_id"])

    # --- member_bank_aliases ---
    op.create_table(
        "member_bank_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("alias_text", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id", "alias_text", name="uq_member_alias"),
    )
    op.create_index("ix_member_bank_aliases_member_id", "member_bank_aliases", ["member_id"])
    op.create_index("ix_member_bank_aliases_alias_text", "member_bank_aliases", ["alias_text"])

    # --- member_claims ---
    op.create_table(
        "member_claims",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("creditor_member_id", sa.Integer(), nullable=True),
        sa.Column("claim_type", claim_type_col, nullable=False),
        sa.Column("fiscal_year_id", sa.Integer(), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("merch_order_id", sa.Integer(), nullable=True),
        sa.Column("expected_rappen", sa.Integer(), nullable=False),
        sa.Column("paid_rappen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", claim_status_col, nullable=False, server_default="OFFEN"),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creditor_member_id"], ["members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fiscal_year_id"], ["fiscal_years.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["merch_order_id"], ["merch_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_member_claims_member_id", "member_claims", ["member_id"])
    op.create_index("ix_member_claims_creditor_member_id", "member_claims", ["creditor_member_id"])
    op.create_index("ix_member_claims_claim_type", "member_claims", ["claim_type"])
    op.create_index("ix_member_claims_fiscal_year_id", "member_claims", ["fiscal_year_id"])
    op.create_index("ix_member_claims_event_id", "member_claims", ["event_id"])
    op.create_index("ix_member_claims_merch_order_id", "member_claims", ["merch_order_id"])
    op.create_index("ix_member_claims_status", "member_claims", ["status"])


def downgrade():
    bind = op.get_bind()

    op.drop_index("ix_member_claims_status", table_name="member_claims")
    op.drop_index("ix_member_claims_merch_order_id", table_name="member_claims")
    op.drop_index("ix_member_claims_event_id", table_name="member_claims")
    op.drop_index("ix_member_claims_fiscal_year_id", table_name="member_claims")
    op.drop_index("ix_member_claims_claim_type", table_name="member_claims")
    op.drop_index("ix_member_claims_creditor_member_id", table_name="member_claims")
    op.drop_index("ix_member_claims_member_id", table_name="member_claims")
    op.drop_table("member_claims")

    op.drop_index("ix_member_bank_aliases_alias_text", table_name="member_bank_aliases")
    op.drop_index("ix_member_bank_aliases_member_id", table_name="member_bank_aliases")
    op.drop_table("member_bank_aliases")

    op.drop_index("ix_bank_transactions_booking_id", table_name="bank_transactions")
    op.drop_index("ix_bank_transactions_status", table_name="bank_transactions")
    op.drop_index("ix_bank_transactions_line_key", table_name="bank_transactions")
    op.drop_index("ix_bank_transactions_parent_id", table_name="bank_transactions")
    op.drop_index("ix_bank_transactions_zkb_ref", table_name="bank_transactions")
    op.drop_index("ix_bank_transactions_import_id", table_name="bank_transactions")
    op.drop_table("bank_transactions")

    op.drop_index(
        "ix_bank_statement_imports_fiscal_year_id",
        table_name="bank_statement_imports",
    )
    op.drop_table("bank_statement_imports")

    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_constraint("fk_events_bill_payer_member_id", type_="foreignkey")
        batch_op.drop_column("bill_payer_member_id")
        batch_op.drop_column("bill_paid_by")

    with op.batch_alter_table("fiscal_years", schema=None) as batch_op:
        batch_op.drop_column("membership_fee_rappen")

    if bind.dialect.name == "postgresql":
        bill_paid_by.drop(bind, checkfirst=True)
        claim_status.drop(bind, checkfirst=True)
        claim_type.drop(bind, checkfirst=True)
        bank_tx_status.drop(bind, checkfirst=True)
    # bookingdirection gehoert zu Phase 4 (bookings) – hier nicht droppen.
    # PostgreSQL kann Enum-Werte nicht entfernen; ESSEN_BUCHHALTUNG bleibt in eventtype.
