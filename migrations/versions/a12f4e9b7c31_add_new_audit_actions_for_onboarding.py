"""add onboarding audit actions to auditaction enum

Revision ID: a12f4e9b7c31
Revises: 6f9a2d1c4b7e
Create Date: 2026-04-27 15:50:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "a12f4e9b7c31"
down_revision = "6f9a2d1c4b7e"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'USE_ONBOARDING_TOKEN'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'SEND_ONBOARDING_MAIL'")


def downgrade():
    # PostgreSQL enums support no simple, safe DROP VALUE.
    # Keeping values is acceptable for rollback compatibility.
    pass
