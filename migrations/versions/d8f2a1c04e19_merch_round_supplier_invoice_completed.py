"""Merch-Runde: Beleg-Schritt abgeschlossen (Workflow Schritt zurueck).

Revision ID: d8f2a1c04e19
Revises: c4e8a9012b71
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = 'd8f2a1c04e19'
down_revision = 'c4e8a9012b71'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'merch_rounds',
        sa.Column('supplier_invoice_completed_at', sa.DateTime(), nullable=True),
    )
    op.execute(
        """
        UPDATE merch_rounds
        SET supplier_invoice_completed_at = COALESCE(ordered_at, updated_at, created_at)
        WHERE (supplier_invoice_drive_file_id IS NOT NULL
               OR supplier_invoice_total_rappen IS NOT NULL)
          AND status IN ('ORDERED_AT_SUPPLIER', 'DELIVERED', 'CLOSED')
        """
    )


def downgrade():
    op.drop_column('merch_rounds', 'supplier_invoice_completed_at')
