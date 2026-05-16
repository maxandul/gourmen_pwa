"""phase 10: Merch audit actions

Revision ID: b7c2e8f91d04
Revises: a9c81e2d4f03
Create Date: 2026-05-16

PostgreSQL: ALTER TYPE auditaction ADD VALUE IF NOT EXISTS ...
SQLite: keine Enum-Erweiterung noetig.
"""

from alembic import op


revision = "b7c2e8f91d04"
down_revision = "a9c81e2d4f03"
branch_labels = None
depends_on = None


NEW_AUDIT_ACTION_VALUES = (
    "MERCH_SUPPLIER_CREATED",
    "MERCH_SUPPLIER_UPDATED",
    "MERCH_ARTICLE_CREATED",
    "MERCH_ARTICLE_UPDATED",
    "MERCH_ARTICLE_ARCHIVED",
    "MERCH_ROUND_CREATED",
    "MERCH_ROUND_OPENED",
    "MERCH_ROUND_LOCKED",
    "MERCH_ROUND_REOPENED",
    "MERCH_ROUND_ORDERED_AT_SUPPLIER",
    "MERCH_ROUND_DELIVERED",
    "MERCH_ROUND_CLOSED",
    "MERCH_ROUND_CANCELLED",
    "MERCH_ORDER_CONFIRMED",
    "MERCH_ORDER_CANCELLED",
    "MERCH_ORDER_PICKED_UP",
    "MERCH_ORDER_PAID",
    "MERCH_SUPPLIER_INVOICE_UPLOADED",
)


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for value in NEW_AUDIT_ACTION_VALUES:
        op.execute(f"ALTER TYPE auditaction ADD VALUE IF NOT EXISTS '{value}'")


def downgrade():
    pass
