"""add ical_token to members (iCal feed per member, Phase 5)

Revision ID: f8a91c2d4e10
Revises: e3c5f9a6b423
Create Date: 2026-05-14

Capability: docs/capabilities/calendar.md
"""

from alembic import op
import sqlalchemy as sa


revision = "f8a91c2d4e10"
down_revision = "e3c5f9a6b423"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("members", schema=None) as batch_op:
        batch_op.add_column(sa.Column("ical_token", sa.String(length=64), nullable=True))
        batch_op.create_index("ix_members_ical_token", ["ical_token"], unique=True)


def downgrade():
    with op.batch_alter_table("members", schema=None) as batch_op:
        batch_op.drop_index("ix_members_ical_token")
        batch_op.drop_column("ical_token")
