"""Phase 10 Merch: Neue Tabellen v2 (Lieferanten, Sortiment, Runden, Bestellungen).

Revision ID: a9c81e2d4f03
Revises: f8e91d4c3b2a
Create Date: 2026-05-15

Schema gemaess docs/capabilities/merch.md Sektion 6.

PostgreSQL: eigene Enums `merchroundstatus`, `merchorderv2status` (Alt-Shop nutzt
weiter `orderstatus` auf `merch_orders_legacy`).

SQLite: Status-Spalten als VARCHAR(32).

Index `ix_nv2_merch_variants_article_id` und `ix_nv2_merch_order_items_order_id`:
einzigartige Namen neben Legacy (`merch_*_legacy`), da Indexnamen DB-weit eindeutig
sein muessen (SQLite/PostgreSQL).

Downgrade: dropt nur die neuen Tabellen + die beiden neuen Enum-Typen (PG).
"""

from alembic import op
import sqlalchemy as sa


revision = "a9c81e2d4f03"
down_revision = "f8e91d4c3b2a"
branch_labels = None
depends_on = None


ROUND_STATUS_VALUES = (
    "DRAFT",
    "OPEN",
    "LOCKED",
    "ORDERED_AT_SUPPLIER",
    "DELIVERED",
    "CLOSED",
    "CANCELLED",
)

ORDER_V2_STATUS_VALUES = (
    "DRAFT",
    "CONFIRMED",
    "INVOICED",
    "PICKED_UP",
    "PAID",
    "CANCELLED",
)


def _round_status_column():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return sa.Column(
            "status",
            sa.Enum(
                *ROUND_STATUS_VALUES,
                name="merchroundstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="DRAFT",
        )
    return sa.Column(
        "status",
        sa.String(length=32),
        nullable=False,
        server_default="DRAFT",
    )


def _order_v2_status_column():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return sa.Column(
            "status",
            sa.Enum(
                *ORDER_V2_STATUS_VALUES,
                name="merchorderv2status",
                create_type=False,
            ),
            nullable=False,
            server_default="DRAFT",
        )
    return sa.Column(
        "status",
        sa.String(length=32),
        nullable=False,
        server_default="DRAFT",
    )


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        sa.Enum(*ROUND_STATUS_VALUES, name="merchroundstatus").create(
            bind, checkfirst=True
        )
        sa.Enum(*ORDER_V2_STATUS_VALUES, name="merchorderv2status").create(
            bind, checkfirst=True
        )

    op.create_table(
        "merch_suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("contact_email", sa.String(length=200), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "merch_articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("list_price_rappen", sa.Integer(), nullable=False),
        sa.Column("image_drive_file_id", sa.String(length=200), nullable=True),
        sa.Column("variant_schema", sa.JSON(), nullable=True),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["merch_suppliers.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_merch_articles_supplier_id",
        "merch_articles",
        ["supplier_id"],
        unique=False,
    )

    op.create_table(
        "merch_variants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("list_price_rappen", sa.Integer(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["article_id"], ["merch_articles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Namen mit nv2-Prefix: SQLite/Postgres haben schema-globale Indexnamen;
    # Legacy `merch_*_legacy` behalten z.B. ix_merch_variants_article_id.
    op.create_index(
        "ix_nv2_merch_variants_article_id",
        "merch_variants",
        ["article_id"],
        unique=False,
    )

    op.create_table(
        "merch_rounds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        _round_status_column(),
        sa.Column("deadline_communicated", sa.Date(), nullable=True),
        sa.Column(
            "subsidy_per_member_rappen",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "supplier_invoice_drive_file_id",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "supplier_invoice_total_rappen", sa.Integer(), nullable=True
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("marketing_chief_id", sa.Integer(), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=True),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("ordered_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["marketing_chief_id"],
            ["members.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_merch_rounds_status",
        "merch_rounds",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_merch_rounds_marketing_chief_id",
        "merch_rounds",
        ["marketing_chief_id"],
        unique=False,
    )

    op.create_table(
        "merch_round_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column(
            "list_price_snapshot_rappen", sa.Integer(), nullable=False
        ),
        sa.Column(
            "effective_supplier_price_rappen", sa.Integer(), nullable=True
        ),
        sa.Column("member_price_rappen", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["round_id"], ["merch_rounds.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"], ["merch_variants.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "round_id", "variant_id", name="uq_round_variant"
        ),
    )
    op.create_index(
        "ix_merch_round_items_round_id",
        "merch_round_items",
        ["round_id"],
        unique=False,
    )
    op.create_index(
        "ix_merch_round_items_variant_id",
        "merch_round_items",
        ["variant_id"],
        unique=False,
    )

    op.create_table(
        "merch_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        _order_v2_status_column(),
        sa.Column("gross_amount_rappen", sa.Integer(), nullable=True),
        sa.Column("subsidy_amount_rappen", sa.Integer(), nullable=True),
        sa.Column("member_amount_due_rappen", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("invoiced_at", sa.DateTime(), nullable=True),
        sa.Column("picked_up_at", sa.DateTime(), nullable=True),
        sa.Column("picked_up_by_member_id", sa.Integer(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("paid_by_member_id", sa.Integer(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["member_id"], ["members.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["paid_by_member_id"], ["members.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["picked_up_by_member_id"], ["members.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["round_id"], ["merch_rounds.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "round_id", "member_id", name="uq_round_member"
        ),
    )
    op.create_index(
        "ix_merch_orders_member",
        "merch_orders",
        ["member_id"],
        unique=False,
    )
    op.create_index(
        "ix_merch_orders_round_status",
        "merch_orders",
        ["round_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_merch_orders_round_id",
        "merch_orders",
        ["round_id"],
        unique=False,
    )

    op.create_table(
        "merch_order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("round_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "unit_price_at_confirm_rappen", sa.Integer(), nullable=False
        ),
        sa.Column("unit_price_final_rappen", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["merch_orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["round_item_id"],
            ["merch_round_items.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id", "round_item_id", name="uq_order_round_item"
        ),
    )
    op.create_index(
        "ix_nv2_merch_order_items_order_id",
        "merch_order_items",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_merch_order_items_round_item_id",
        "merch_order_items",
        ["round_item_id"],
        unique=False,
    )


def downgrade():
    bind = op.get_bind()

    op.drop_index("ix_merch_order_items_round_item_id", table_name="merch_order_items")
    op.drop_index("ix_nv2_merch_order_items_order_id", table_name="merch_order_items")
    op.drop_table("merch_order_items")

    op.drop_index("ix_merch_orders_round_id", table_name="merch_orders")
    op.drop_index("ix_merch_orders_round_status", table_name="merch_orders")
    op.drop_index("ix_merch_orders_member", table_name="merch_orders")
    op.drop_table("merch_orders")

    op.drop_index("ix_merch_round_items_variant_id", table_name="merch_round_items")
    op.drop_index("ix_merch_round_items_round_id", table_name="merch_round_items")
    op.drop_table("merch_round_items")

    op.drop_index("ix_merch_rounds_marketing_chief_id", table_name="merch_rounds")
    op.drop_index("ix_merch_rounds_status", table_name="merch_rounds")
    op.drop_table("merch_rounds")

    op.drop_index("ix_merch_variants_article_id", table_name="merch_variants")
    op.drop_table("merch_variants")

    op.drop_index("ix_merch_articles_supplier_id", table_name="merch_articles")
    op.drop_table("merch_articles")

    op.drop_table("merch_suppliers")

    if bind.dialect.name == "postgresql":
        sa.Enum(*ORDER_V2_STATUS_VALUES, name="merchorderv2status").drop(
            bind, checkfirst=True
        )
        sa.Enum(*ROUND_STATUS_VALUES, name="merchroundstatus").drop(
            bind, checkfirst=True
        )
