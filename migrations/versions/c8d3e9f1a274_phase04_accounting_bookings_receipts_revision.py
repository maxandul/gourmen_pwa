"""Phase 4 – Buchhaltung Teil 2: Buchungen, Belege, Revision.

Revision ID: c8d3e9f1a274
Revises: b1f7a4c2d590
Create Date: 2026-06-10

Neue Tabellen: bookings, receipts, revision_comments, revision_approvals.
Spezifikation: docs/capabilities/accounting.md Sektion 4.3 / 4.4 / 4.6 / 4.7.
"""

from alembic import op
import sqlalchemy as sa


revision = "c8d3e9f1a274"
down_revision = "b1f7a4c2d590"
branch_labels = None
depends_on = None


booking_direction = sa.Enum("IN", "OUT", name="bookingdirection")


def upgrade():
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fiscal_year_id", sa.Integer(), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount_rappen", sa.Integer(), nullable=False),
        sa.Column("direction", booking_direction, nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("member_id", sa.Integer(), nullable=True),
        sa.Column("payment_ref", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["fiscal_year_id"], ["fiscal_years.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["members.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookings_fiscal_year_id", "bookings", ["fiscal_year_id"])
    op.create_index("ix_bookings_account_id", "bookings", ["account_id"])
    op.create_index("ix_bookings_event_id", "bookings", ["event_id"])
    op.create_index("ix_bookings_member_id", "bookings", ["member_id"])

    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("drive_file_id", sa.String(length=255), nullable=False),
        sa.Column("drive_file_name", sa.String(length=255), nullable=False),
        sa.Column("drive_folder_id", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=True),
        sa.Column("uploader_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("suggested_account_id", sa.Integer(), nullable=True),
        sa.Column("suggested_event_id", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("ocr_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uploader_id"], ["members.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["suggested_account_id"], ["accounts.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["suggested_event_id"], ["events.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_receipts_booking_id", "receipts", ["booking_id"])
    op.create_index("ix_receipts_uploader_id", "receipts", ["uploader_id"])

    op.create_table(
        "revision_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("fiscal_year_id", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["fiscal_year_id"], ["fiscal_years.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["author_id"], ["members.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_revision_comments_booking_id", "revision_comments", ["booking_id"]
    )
    op.create_index(
        "ix_revision_comments_fiscal_year_id", "revision_comments", ["fiscal_year_id"]
    )

    op.create_table(
        "revision_approvals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fiscal_year_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("report_drive_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["fiscal_year_id"], ["fiscal_years.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["reviewer_id"], ["members.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fiscal_year_id", name="uq_revision_approvals_fiscal_year"),
    )


def downgrade():
    op.drop_table("revision_approvals")

    op.drop_index("ix_revision_comments_fiscal_year_id", table_name="revision_comments")
    op.drop_index("ix_revision_comments_booking_id", table_name="revision_comments")
    op.drop_table("revision_comments")

    op.drop_index("ix_receipts_uploader_id", table_name="receipts")
    op.drop_index("ix_receipts_booking_id", table_name="receipts")
    op.drop_table("receipts")

    op.drop_index("ix_bookings_member_id", table_name="bookings")
    op.drop_index("ix_bookings_event_id", table_name="bookings")
    op.drop_index("ix_bookings_account_id", table_name="bookings")
    op.drop_index("ix_bookings_fiscal_year_id", table_name="bookings")
    op.drop_table("bookings")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        booking_direction.drop(bind, checkfirst=True)
