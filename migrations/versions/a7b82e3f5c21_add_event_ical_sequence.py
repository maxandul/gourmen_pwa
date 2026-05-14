"""add ical_sequence to events (iCal SEQUENCE/RFC 5545, Phase 5)

Revision ID: a7b82e3f5c21
Revises: f8a91c2d4e10
Create Date: 2026-05-14

Capability: docs/capabilities/calendar.md
"""

from alembic import op
import sqlalchemy as sa


revision = "a7b82e3f5c21"
down_revision = "f8a91c2d4e10"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "ical_sequence",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )


def downgrade():
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_column("ical_sequence")
