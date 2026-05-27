"""Merch-Runde: mehrere Lieferantenbelege (Drive).

Revision ID: e7f3b2a91c04
Revises: d8f2a1c04e19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = 'e7f3b2a91c04'
down_revision = 'd8f2a1c04e19'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'merch_round_supplier_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('round_id', sa.Integer(), nullable=False),
        sa.Column('drive_file_id', sa.String(length=200), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['round_id'], ['merch_rounds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_merch_round_supplier_invoices_round_id'),
        'merch_round_supplier_invoices',
        ['round_id'],
        unique=False,
    )
    op.execute(
        """
        INSERT INTO merch_round_supplier_invoices (round_id, drive_file_id, original_filename, created_at)
        SELECT id, supplier_invoice_drive_file_id, NULL, COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
        FROM merch_rounds
        WHERE supplier_invoice_drive_file_id IS NOT NULL
        """
    )


def downgrade():
    op.drop_index(
        op.f('ix_merch_round_supplier_invoices_round_id'),
        table_name='merch_round_supplier_invoices',
    )
    op.drop_table('merch_round_supplier_invoices')
