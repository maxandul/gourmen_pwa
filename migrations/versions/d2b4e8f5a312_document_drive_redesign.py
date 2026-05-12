"""document drive redesign - alte URL-Records loeschen, Drive-Felder anlegen

Revision ID: d2b4e8f5a312
Revises: c1a3d8e4f201
Create Date: 2026-05-12 21:10:00.000000

Drive-Capability Phase 03 Migration 2 von 3.

Strategie (Capability Sektion 6.4): Alle bestehenden Document-Records werden
geloescht (Andreas-Freigabe: «alles bisher verwerfen»). Die alten Spalten
`url`, `visibility`, `deleted_at` werden entfernt, das alte Category-Enum
durch das neue ersetzt. Neue Drive-Felder und ein Status-Enum kommen dazu.

Downgrade ist bewusst nicht implementiert: Drive-Verknuepfungen sind nicht
reversibel, eine zurueckgenommene Migration wuerde verwaiste Drive-Files
hinterlassen.
"""

from alembic import op
import sqlalchemy as sa


revision = "d2b4e8f5a312"
down_revision = "c1a3d8e4f201"
branch_labels = None
depends_on = None


NEW_CATEGORY_VALUES = (
    "STATUTEN",
    "VEREINSFUEHRUNG",
    "FINANZEN",
    "VERTRAEGE",
    "REISEN_EVENTS",
    "MEDIEN",
    "SONSTIGES",
)
STATUS_VALUES = ("ACTIVE", "ARCHIVED")


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    # 1. Alle bestehenden URL-only-Records loeschen.
    op.execute(sa.text("DELETE FROM documents"))

    # 2. PostgreSQL: alte Enum-Typen droppen, damit sie neu angelegt werden
    #    koennen. SQLite verwendet CHECK-Constraints und ist hier toleranter.
    if dialect == "postgresql":
        # Alte Enums weg, neue anlegen.
        op.execute("DROP TYPE IF EXISTS documentcategory")
        op.execute("DROP TYPE IF EXISTS documentvisibility")
        category_enum = sa.Enum(*NEW_CATEGORY_VALUES, name="documentcategory")
        status_enum = sa.Enum(*STATUS_VALUES, name="documentstatus")
        category_enum.create(bind, checkfirst=True)
        status_enum.create(bind, checkfirst=True)

    # 3. Spalten-Umbau via batch (kompatibel mit SQLite).
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.drop_column("url")
        batch_op.drop_column("visibility")
        batch_op.drop_column("deleted_at")

        # category-Spalte komplett ersetzen: alten Enum-Wert durch neuen ersetzen.
        # Wir entfernen die Spalte und legen sie neu mit dem neuen Enum an,
        # weil sich der Wertbereich nicht ueberlappt (alt: VEREIN/EVENT/...).
        batch_op.drop_column("category")
        batch_op.add_column(
            sa.Column(
                "category",
                sa.Enum(*NEW_CATEGORY_VALUES, name="documentcategory"),
                nullable=False,
            )
        )

        batch_op.add_column(
            sa.Column(
                "status",
                sa.Enum(*STATUS_VALUES, name="documentstatus"),
                nullable=False,
                server_default="ACTIVE",
            )
        )

        batch_op.add_column(
            sa.Column("drive_file_id", sa.String(length=100), nullable=False)
        )
        batch_op.add_column(
            sa.Column("drive_web_view_link", sa.String(length=500), nullable=True)
        )
        batch_op.add_column(
            sa.Column("mime_type", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(sa.Column("size_bytes", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column("archived_by_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("last_synced_at", sa.DateTime(), nullable=True)
        )

        # uploader_id wird nullable (per Re-Sync importierte Files koennen
        # keinen Member als Uploader haben, siehe Capability Sektion 9.3 / 19).
        batch_op.alter_column(
            "uploader_id", existing_type=sa.Integer(), nullable=True
        )

        batch_op.create_foreign_key(
            "fk_documents_archived_by_id_members",
            "members",
            ["archived_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

        batch_op.create_index(
            "ix_documents_drive_file_id", ["drive_file_id"], unique=True
        )
        batch_op.create_index("ix_documents_status", ["status"], unique=False)
        batch_op.create_index("ix_documents_category", ["category"], unique=False)
        batch_op.create_index(
            "ix_documents_status_category", ["status", "category"], unique=False
        )


def downgrade():
    raise NotImplementedError(
        "Downgrade nicht implementiert: Drive-Verknuepfungen sind nicht "
        "reversibel. Siehe docs/capabilities/drive.md, Sektion 6.4."
    )
