"""Phase 4 – Beleg-Anzeigename.

Revision ID: e1a2c7b4d905
Revises: c8d3e9f1a274
Create Date: 2026-07-03

Ergaenzt receipts.display_name (kurzer Anzeige-Name zusaetzlich zum langen
Drive-Dateinamen). Spezifikation: docs/capabilities/accounting.md Sektion 4.4.
"""

from alembic import op
import sqlalchemy as sa


revision = "e1a2c7b4d905"
down_revision = "c8d3e9f1a274"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "receipts",
        sa.Column("display_name", sa.String(length=120), nullable=True),
    )


def downgrade():
    op.drop_column("receipts", "display_name")
