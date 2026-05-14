"""add calendar feed audit actions (Phase 5 iCal)

Revision ID: c3d94e1f2a56
Revises: a7b82e3f5c21
Create Date: 2026-05-14
"""

from alembic import op


revision = "c3d94e1f2a56"
down_revision = "a7b82e3f5c21"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for val in (
        "CALENDAR_FEED_ENABLED",
        "CALENDAR_FEED_REGENERATED",
        "CALENDAR_FEED_DISABLED",
    ):
        op.execute(f"ALTER TYPE auditaction ADD VALUE IF NOT EXISTS '{val}'")


def downgrade():
    pass
