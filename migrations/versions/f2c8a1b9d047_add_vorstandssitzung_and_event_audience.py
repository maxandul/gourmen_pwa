"""Add VORSTANDSSITZUNG to EventType + events.audience

Revision ID: f2c8a1b9d047
Revises: e1a2c7b4d905
Create Date: 2026-07-13

Board meetings (Vorstandssitzung) are a dedicated event type with
audience scoping (all | board). Spec: docs/DOMAIN.md, docs/capabilities/calendar.md §16.1.
"""

from alembic import op
import sqlalchemy as sa


revision = "f2c8a1b9d047"
down_revision = "e1a2c7b4d905"
branch_labels = None
depends_on = None

audience_enum = sa.Enum("all", "board", name="eventaudience")


def upgrade():
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'VORSTANDSSITZUNG'")
        audience_enum.create(bind, checkfirst=True)

    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "audience",
                audience_enum,
                nullable=False,
                server_default="all",
            )
        )
        batch_op.create_index("ix_events_audience", ["audience"], unique=False)


def downgrade():
    bind = op.get_bind()
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_index("ix_events_audience")
        batch_op.drop_column("audience")

    if bind.dialect.name == "postgresql":
        audience_enum.drop(bind, checkfirst=True)
    # PostgreSQL cannot easily DROP ENUM values from eventtype; leave VORSTANDSSITZUNG.
