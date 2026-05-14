"""Document model - Vereinsdokumente im Google Shared Drive.

Drive-Capability Phase 03 (siehe docs/capabilities/drive.md).
"""

from datetime import datetime
from enum import Enum

from backend.extensions import db


class DocumentCategory(Enum):
    """Top-Level-Folder im Shared Drive (Capability Sektion 5.1).

    Werte sind so gewaehlt, dass sie direkt als Folder-Namen im Drive
    verwendet werden koennen (mit Umlauten, da Drive Unicode unterstuetzt).
    """

    STATUTEN = "STATUTEN"
    VEREINSFUEHRUNG = "VEREINSFUEHRUNG"
    FINANZEN = "FINANZEN"
    VERTRAEGE = "VERTRAEGE"
    REISEN_EVENTS = "REISEN_EVENTS"
    MEDIEN = "MEDIEN"
    SONSTIGES = "SONSTIGES"


class DocumentStatus(Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


# Klartext-Labels fuer UI (Deutsch, Capability Sektion 5.1)
CATEGORY_LABELS = {
    DocumentCategory.STATUTEN: "Statuten",
    DocumentCategory.VEREINSFUEHRUNG: "Vereinsführung",
    DocumentCategory.FINANZEN: "Finanzen",
    DocumentCategory.VERTRAEGE: "Verträge",
    DocumentCategory.REISEN_EVENTS: "Reisen und Events",
    DocumentCategory.MEDIEN: "Medien",
    DocumentCategory.SONSTIGES: "Sonstiges",
}

# Drive-Folder-Namen (mit Umlauten und Bindestrich – siehe Capability 5.1).
# Mussen mit dem Setup-Script und der Folder-Initialisierung uebereinstimmen.
CATEGORY_FOLDER_NAMES = {
    DocumentCategory.STATUTEN: "Statuten",
    DocumentCategory.VEREINSFUEHRUNG: "Vereinsführung",
    DocumentCategory.FINANZEN: "Finanzen",
    DocumentCategory.VERTRAEGE: "Verträge",
    DocumentCategory.REISEN_EVENTS: "Reisen-und-Events",
    DocumentCategory.MEDIEN: "Medien",
    DocumentCategory.SONSTIGES: "Sonstiges",
}

# Spezieller Folder-Name fuer den Archiv-Folder (Status = ARCHIVED).
ARCHIVE_FOLDER_NAME = "Archiv"


class Document(db.Model):
    """Vereinsdokument im Google Shared Drive.

    DB ist Source-of-Truth fuer Metadaten + Status; Drive ist Source-of-Truth
    fuer den Datei-Inhalt. Atomare Operationen halten beide konsistent
    (siehe DriveStorageService).
    """

    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.Enum(DocumentCategory), nullable=False, index=True)
    status = db.Column(
        db.Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.ACTIVE,
        server_default=DocumentStatus.ACTIVE.value,
        index=True,
    )

    # Drive-Identitaet
    drive_file_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    drive_web_view_link = db.Column(db.String(500))

    # Datei-Metadaten
    mime_type = db.Column(db.String(100))
    size_bytes = db.Column(db.BigInteger)
    checksum = db.Column(db.String(64))

    # Beziehungen
    event_id = db.Column(
        db.Integer, db.ForeignKey("events.id", ondelete="SET NULL")
    )
    # uploader_id ist nullable, weil per Re-Sync importierte Files keinen
    # zuordbaren Uploader haben muessen (Capability Sektion 9.3 / 19).
    uploader_id = db.Column(
        db.Integer, db.ForeignKey("members.id", ondelete="SET NULL")
    )

    # Lifecycle
    archived_at = db.Column(db.DateTime)
    archived_by_id = db.Column(
        db.Integer, db.ForeignKey("members.id", ondelete="SET NULL")
    )

    # Sync-Helper
    last_synced_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.Index("ix_documents_status_category", "status", "category"),
    )

    def __repr__(self):
        return f"<Document {self.id}: {self.title}>"

    @property
    def is_archived(self) -> bool:
        return self.status == DocumentStatus.ARCHIVED

    @property
    def display_category(self) -> str:
        return CATEGORY_LABELS.get(self.category, str(self.category))

    @property
    def display_status(self) -> str:
        return "Archiviert" if self.is_archived else "Aktiv"

    @property
    def folder_name(self) -> str:
        """Drive-Folder-Name fuer die aktuelle Kategorie (Aktiv-Folder).

        Wird auch bei archivierten Documents fuer den Wiederherstellungs-Pfad
        gebraucht – `category` bleibt erhalten, wenn `status=ARCHIVED`.
        """
        return CATEGORY_FOLDER_NAMES.get(self.category, "Sonstiges")
