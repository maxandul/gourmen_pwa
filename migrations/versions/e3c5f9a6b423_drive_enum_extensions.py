"""drive enum extensions - GOOGLE_EMAIL_VERIFY + DOCUMENT_* + DRIVE_* audit actions

Revision ID: e3c5f9a6b423
Revises: d2b4e8f5a312
Create Date: 2026-05-12 21:20:00.000000

Drive-Capability Phase 03 Migration 3 von 3.

Erweitert die beiden bestehenden Enum-Typen:
- `authtokenpurpose`: GOOGLE_EMAIL_VERIFY
- `auditaction`: DOCUMENT_UPLOADED, DOCUMENT_RENAMED, DOCUMENT_MOVED,
  DOCUMENT_ARCHIVED, DOCUMENT_RESTORED, DOCUMENT_PERMANENTLY_DELETED,
  DOCUMENT_AUTO_SYNCED, DRIVE_MEMBERSHIP_ADDED, DRIVE_MEMBERSHIP_REMOVED,
  DRIVE_MEMBERSHIP_FAILED, DRIVE_QUOTA_EXCEEDED, DRIVE_RESYNC_RAN,
  GOOGLE_EMAIL_VERIFY_REQUESTED, GOOGLE_EMAIL_VERIFIED

In PostgreSQL via `ALTER TYPE ... ADD VALUE`. SQLite (lokale Entwicklung)
verwendet keine echten Enums – dort sind die Werte direkt nutzbar.
"""

from alembic import op


revision = "e3c5f9a6b423"
down_revision = "d2b4e8f5a312"
branch_labels = None
depends_on = None


NEW_TOKEN_PURPOSE_VALUES = ("GOOGLE_EMAIL_VERIFY",)
NEW_AUDIT_ACTION_VALUES = (
    "DOCUMENT_UPLOADED",
    "DOCUMENT_RENAMED",
    "DOCUMENT_MOVED",
    "DOCUMENT_ARCHIVED",
    "DOCUMENT_RESTORED",
    "DOCUMENT_PERMANENTLY_DELETED",
    "DOCUMENT_AUTO_SYNCED",
    "DRIVE_MEMBERSHIP_ADDED",
    "DRIVE_MEMBERSHIP_REMOVED",
    "DRIVE_MEMBERSHIP_FAILED",
    "DRIVE_QUOTA_EXCEEDED",
    "DRIVE_RESYNC_RAN",
    "GOOGLE_EMAIL_VERIFY_REQUESTED",
    "GOOGLE_EMAIL_VERIFIED",
)


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite und andere: Enums sind dort effektiv VARCHARs.
        return

    for value in NEW_TOKEN_PURPOSE_VALUES:
        op.execute(f"ALTER TYPE authtokenpurpose ADD VALUE IF NOT EXISTS '{value}'")

    for value in NEW_AUDIT_ACTION_VALUES:
        op.execute(f"ALTER TYPE auditaction ADD VALUE IF NOT EXISTS '{value}'")


def downgrade():
    # PostgreSQL erlaubt keinen einfachen DROP VALUE. Werte bleiben ohne
    # Schaden in den Enum-Typen erhalten (Capability Sektion 6.4).
    pass
