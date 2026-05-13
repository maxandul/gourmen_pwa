"""add google_email fields to members

Revision ID: c1a3d8e4f201
Revises: a12f4e9b7c31
Create Date: 2026-05-12 21:00:00.000000

Drive-Capability Phase 03 Migration 1 von 3: bereitet die Member-Tabelle auf
Google-Drive-Membership vor (siehe docs/capabilities/drive.md, Sektion 4 + 6).

Hinweis: Der zugehoerige Token-Purpose `GOOGLE_EMAIL_VERIFY` wird in
Migration 3 (Enum-Erweiterungen) hinzugefuegt – getrennt, weil Enum-Adds
in PostgreSQL nicht in einer Transaktion mit ALTER TABLE laufen koennen.
"""

from alembic import op
import sqlalchemy as sa


revision = "c1a3d8e4f201"
down_revision = "a12f4e9b7c31"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("members", schema=None) as batch_op:
        batch_op.add_column(sa.Column("google_email", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column(
                "google_email_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("google_email_verified_at", sa.DateTime(), nullable=True))
        batch_op.create_index(
            "ix_members_google_email", ["google_email"], unique=False
        )


def downgrade():
    raise NotImplementedError(
        "Downgrade nicht implementiert: Drive-Membership ist nicht "
        "reversibel (Drive-Permissions wuerden verwaisen). Siehe "
        "docs/capabilities/drive.md, Sektion 6.4."
    )
