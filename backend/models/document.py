"""Document model – Vereinsdokumente im Google Shared Drive.

Drive-Browser-Modell (Phase 9). Spezifikation: docs/capabilities/drive.md.
"""

from datetime import datetime

from backend.extensions import db


class Document(db.Model):
    """Schlanker DB-Cache zu einer Drive-Datei.

    Drive ist Source of Truth fuer Filename, Ordner, MIME und Groesse.
    """

    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)

    drive_file_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    drive_parent_id = db.Column(db.String(100), nullable=False, index=True)

    uploader_id = db.Column(
        db.Integer, db.ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    event_id = db.Column(
        db.Integer, db.ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )

    last_seen_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Document {self.id}: {self.drive_file_id}>"
