"""Phase 9 – Document-Modell fuer Drive-Browser (Folder-Hierarchie).

Revision ID: d4e8f1a2b903
Revises: c3d94e1f2a56
Create Date: 2026-05-15

Trockene Migration (siehe docs/capabilities/drive.md 6.4): bestehende
`documents`-Zeilen werden geloescht. Spalten werden auf den schlanken Cache
reduziert (`drive_parent_id`, `last_seen_at`). Postgres-Enums
`documentcategory` und `documentstatus` werden entfernt.

Ergaenzt `auditaction` um DOCUMENT_AUTO_IMPORTED und DOCUMENT_AUTO_REMOVED.

Downgrade: nicht unterstuetzt.
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e8f1a2b903"
down_revision = "c3d94e1f2a56"
branch_labels = None
depends_on = None


_DROP_COLUMNS = (
    "title",
    "category",
    "status",
    "archived_at",
    "archived_by_id",
    "mime_type",
    "size_bytes",
    "checksum",
    "drive_web_view_link",
    "updated_at",
    "last_synced_at",
)

_DROP_INDEXES = (
    "ix_documents_status_category",
    "ix_documents_status",
    "ix_documents_category",
)


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    insp = sa.inspect(bind)

    op.execute(sa.text("DELETE FROM documents"))

    if dialect == "postgresql":
        for val in ("DOCUMENT_AUTO_IMPORTED", "DOCUMENT_AUTO_REMOVED"):
            op.execute(f"ALTER TYPE auditaction ADD VALUE IF NOT EXISTS '{val}'")

    existing_cols = {c["name"] for c in insp.get_columns("documents")}
    existing_ix = {i["name"] for i in insp.get_indexes("documents")}
    has_drive_parent = "drive_parent_id" in existing_cols
    has_last_seen = "last_seen_at" in existing_cols

    with op.batch_alter_table("documents", schema=None) as batch_op:
        for ix_name in _DROP_INDEXES:
            if ix_name in existing_ix:
                batch_op.drop_index(ix_name)

        for fk in insp.get_foreign_keys("documents"):
            if fk.get("name") == "fk_documents_archived_by_id_members":
                batch_op.drop_constraint(
                    "fk_documents_archived_by_id_members", type_="foreignkey"
                )
                break

        for col in _DROP_COLUMNS:
            if col in existing_cols:
                batch_op.drop_column(col)

        if not has_drive_parent:
            batch_op.add_column(
                sa.Column("drive_parent_id", sa.String(length=100), nullable=False)
            )
        if not has_last_seen:
            batch_op.add_column(sa.Column("last_seen_at", sa.DateTime(), nullable=True))

        if "ix_documents_drive_parent_id" not in existing_ix:
            batch_op.create_index(
                "ix_documents_drive_parent_id", ["drive_parent_id"], unique=False
            )

    if dialect == "postgresql":
        op.execute(sa.text("DROP TYPE IF EXISTS documentcategory"))
        op.execute(sa.text("DROP TYPE IF EXISTS documentstatus"))


def downgrade():
    raise NotImplementedError(
        "Downgrade nicht implementiert: Phase-9-Drive-Browser-Schema."
    )
