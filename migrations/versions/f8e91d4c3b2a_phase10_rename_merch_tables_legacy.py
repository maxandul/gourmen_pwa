"""Phase 10 Merch: Alte Merch-Tabellen auf _legacy umbenennen.

Revision ID: f8e91d4c3b2a
Revises: d4e8f1a2b903
Create Date: 2026-05-15

Keine Datenmigration; nur RENAME. Neue Tabellen folgen in einer spaeteren Revision.
Downgrade benennt zurueck (reversibel).

Siehe docs/initiatives/workspace-railway/PHASE_10_MERCH.md und
docs/capabilities/merch.md Sektion 21.1.
"""

from alembic import op


revision = "f8e91d4c3b2a"
down_revision = "d4e8f1a2b903"
branch_labels = None
depends_on = None


def upgrade():
    # Reihenfolge: FK-Ziele zuerst umbenennen (PostgreSQL aktualisiert Constraints).
    op.rename_table("merch_articles", "merch_articles_legacy")
    op.rename_table("merch_variants", "merch_variants_legacy")
    op.rename_table("merch_orders", "merch_orders_legacy")
    op.rename_table("merch_order_items", "merch_order_items_legacy")


def downgrade():
    op.rename_table("merch_order_items_legacy", "merch_order_items")
    op.rename_table("merch_orders_legacy", "merch_orders")
    op.rename_table("merch_variants_legacy", "merch_variants")
    op.rename_table("merch_articles_legacy", "merch_articles")
