"""DriveStorageService – Vereinsdokumente im Google Shared Drive.

Authoritative Spezifikation: docs/capabilities/drive.md.

Authentifiziert via Service-Account-Key aus `GOOGLE_SERVICE_ACCOUNT_KEY`
(Base64-encoded JSON), arbeitet auf dem Shared Drive `GOOGLE_DRIVE_ID`.
Alle Schreib-Operationen sind atomar (Drive + DB) oder werfen explizite
Fehler.

Strikte App-Regel: Routes rufen Services, Services rufen Models und externe
APIs. Routes enthalten keine Drive-Aufrufe direkt.
"""

from __future__ import annotations

import base64
import binascii
import io
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import IO, Iterable

from flask import current_app
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from backend.extensions import db
from backend.models.audit_event import AuditAction
from backend.models.document import (
    ARCHIVE_FOLDER_NAME,
    CATEGORY_FOLDER_NAMES,
    Document,
    DocumentCategory,
    DocumentStatus,
)
from backend.models.member import Member
from backend.services.security import SecurityService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class DriveError(Exception):
    """Generischer Drive-Fehler."""


class DriveNotConfiguredError(DriveError):
    """`GOOGLE_SERVICE_ACCOUNT_KEY` oder `GOOGLE_DRIVE_ID` fehlen."""


class DriveQuotaExceededError(DriveError):
    """Shared Drive ist voll (Workspace Starter: 30 GB)."""


class DriveValidationError(DriveError):
    """Validierung gegen MIME-Allowlist, Groessen-Limit, Title-Regeln."""


class DriveSanitizationError(DriveError):
    """SVG kann nicht sicher sanitiziert werden."""


# ---------------------------------------------------------------------------
# Konstanten (Capability Sektion 11)
# ---------------------------------------------------------------------------


MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB Hard-Limit pro Datei
MAX_TITLE_LENGTH = 200

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        # Office & PDF
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        # Text
        "text/plain",
        "application/rtf",
        # Bilder
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/heic",
        "image/heif",
        # Vektorgrafik (mit Sanitization-Pflicht, siehe Capability 11.3)
        "image/svg+xml",
        # Google-native (falls Direkterstellung im Drive)
        "application/vnd.google-apps.document",
        "application/vnd.google-apps.spreadsheet",
        "application/vnd.google-apps.presentation",
    }
)

GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"

# Drive-Scope: voll, weil drive.file fuer Listing-Operationen ueber Folder
# nicht ausreicht (Capability Sektion 3.3). Service-Account ist ohnehin nur
# Mitglied im einen Shared Drive.
DRIVE_SCOPES = ("https://www.googleapis.com/auth/drive",)


# ---------------------------------------------------------------------------
# Result-Datentypen
# ---------------------------------------------------------------------------


@dataclass
class SyncResult:
    """Ergebnis eines per-Document-Auto-Syncs (Capability Sektion 9.2)."""

    document_id: int
    drift_detected: bool = False
    actions: list[str] = field(default_factory=list)
    note: str | None = None


@dataclass
class ResyncReport:
    """Sammlung aus dem Admin-Re-Sync (Capability Sektion 9.3)."""

    imported: int = 0
    archived_in_drive: int = 0
    restored_from_archive: int = 0
    moved: int = 0
    orphans_removed: int = 0
    folders_seen: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return (
            self.imported
            + self.archived_in_drive
            + self.restored_from_archive
            + self.moved
            + self.orphans_removed
        )


# ---------------------------------------------------------------------------
# Filename-Sanitization (Capability Sektion 7.4)
# ---------------------------------------------------------------------------


_ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_MULTI_WHITESPACE = re.compile(r"\s+")


def sanitize_drive_filename(title: str, extension: str | None) -> str:
    """Erzeugt einen Drive-tauglichen Filename aus Titel + Extension.

    - Strippen der unter Drive/OS verbotenen Zeichen
    - Whitespace normalisieren
    - Kuerzen auf max. 150 Zeichen Basisname (zuzueglich Extension)
    - Fallback ``Untitled`` falls nach Sanitization nichts Bedeutungsvolles
      uebrig bleibt (rein aus Bindestrichen/Whitespace bestehend zaehlt
      nicht als gueltiger Titel)

    >>> sanitize_drive_filename('Hallo / Welt', 'pdf')
    'Hallo - Welt.pdf'
    """
    base = title or ""
    base = _ILLEGAL_FILENAME_CHARS.sub("-", base)
    base = _MULTI_WHITESPACE.sub(" ", base).strip()
    base = base[:150].rstrip(". ")
    # Wenn nach Sanitization nichts Bedeutungsvolles uebrig bleibt
    # (z.B. nur Bindestriche aus '///'), Fallback auf "Untitled".
    if not base or not re.search(r"[A-Za-z0-9\u00C0-\u017F]", base):
        base = "Untitled"

    if not extension:
        return base

    ext = extension.lstrip(".").strip()
    return f"{base}.{ext}" if ext else base


# ---------------------------------------------------------------------------
# SVG-Sanitization (Capability Sektion 11.3) – Pflicht fuer Marketing-Use-Case
# ---------------------------------------------------------------------------


# `xlink:href`/`href` Werte muessen entweder leer, ein Fragment (#...) oder
# ein lokaler Pfad sein. Externe Targets (http/https/javascript/data) werden
# entfernt.
_SAFE_SVG_HREF = re.compile(r"^(#|\s*$)")
# Event-Handler-Attribute (onclick, onload, ...) werden generell gestrippt.
_SVG_EVENT_HANDLER_ATTR = re.compile(r"^on[a-z]+$", re.IGNORECASE)
# Tags, die im Output keinen Platz haben (script + foreignObject = Web-Content).
_SVG_FORBIDDEN_TAGS = {"script", "foreignObject", "iframe", "object", "embed"}


def _strip_active_attrs(elem) -> None:
    """Entferne Event-Handler- und unsichere Href-Attribute auf einem Element."""
    for attr_name in list(elem.attrib.keys()):
        attr_local = attr_name.split("}", 1)[1] if "}" in attr_name else attr_name
        if _SVG_EVENT_HANDLER_ATTR.match(attr_local):
            del elem.attrib[attr_name]
            continue
        if attr_local == "href":
            value = (elem.attrib.get(attr_name) or "").strip()
            if not _SAFE_SVG_HREF.match(value):
                del elem.attrib[attr_name]


def sanitize_svg_bytes(svg_bytes: bytes) -> bytes:
    """Strippt aktive Inhalte aus einem SVG.

    - alle `<script>`/`<foreignObject>`/`<iframe>`/etc. Tags entfernen
    - alle `on*`-Event-Handler-Attribute (auch am Root) entfernen
    - alle `xlink:href`/`href` mit Schema (http/javascript/data) entfernen
    - Standard-Entity-/Doctype-Angriffe via `defusedxml` blockieren

    Die Funktion ist konservativ: bei Unsicherheit wird das Element entfernt,
    nicht «repariert». Default-/xlink-Namespaces werden im Output ohne
    `ns0:`-Praefix erhalten.
    """
    try:
        from defusedxml import ElementTree as DefusedET
    except ImportError as exc:  # pragma: no cover - defusedxml ist Pflicht
        raise DriveSanitizationError(
            "defusedxml fehlt. SVG-Sanitization nicht moeglich."
        ) from exc

    import xml.etree.ElementTree as ET

    # Standard-SVG-Namespaces sauber registrieren, damit ElementTree beim
    # Serialize keine kuenstlichen Prefixe (`ns0:`) einfuehrt.
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

    try:
        root = DefusedET.fromstring(svg_bytes)
    except Exception as exc:  # malformed XML / DTD-Angriff
        raise DriveSanitizationError(
            f"SVG ist kein gueltiges XML oder enthaelt blockierte Konstrukte: {exc}"
        ) from exc

    def _local(name: str) -> str:
        return name.split("}", 1)[1] if "}" in name else name

    # Root-Element selbst auch saeubern (z.B. <svg onload="...">).
    _strip_active_attrs(root)

    def _walk(parent: ET.Element) -> None:
        for child in list(parent):
            tag_local = _local(child.tag)
            if tag_local in _SVG_FORBIDDEN_TAGS:
                parent.remove(child)
                continue
            _strip_active_attrs(child)
            _walk(child)

    _walk(root)

    output = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return output


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def _is_transient_drive_error(exc: BaseException) -> bool:
    """Klassifiziert Drive-Fehler in transient vs. permanent.

    Capability Sektion 7.2: 429/5xx und Netzwerk-Timeouts werden retried.
    """
    try:
        from googleapiclient.errors import HttpError
    except ImportError:
        return False

    if isinstance(exc, HttpError):
        status = getattr(exc.resp, "status", None) if hasattr(exc, "resp") else None
        try:
            status = int(status) if status is not None else None
        except (TypeError, ValueError):
            status = None
        return status in {429, 500, 502, 503, 504}

    # Netzwerk-/Timeout-Fehler (httplib2/urllib)
    return isinstance(exc, (TimeoutError, ConnectionError))


_drive_retry = retry(
    retry=retry_if_exception(_is_transient_drive_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    reraise=True,
)


class DriveStorageService:
    """Service-Layer fuer Google Shared Drive Operations.

    Methoden gemaess Capability Sektion 7.1.
    """

    # -- Auth / Client ------------------------------------------------------

    @staticmethod
    def _get_drive_id() -> str:
        drive_id = current_app.config.get("GOOGLE_DRIVE_ID")
        if not drive_id:
            raise DriveNotConfiguredError("GOOGLE_DRIVE_ID ist nicht konfiguriert.")
        return drive_id

    @staticmethod
    def _load_credentials():
        try:
            from google.oauth2 import service_account
        except ImportError as exc:
            raise DriveError(
                "google-auth ist nicht installiert. requirements.txt aktualisieren."
            ) from exc

        raw_key = current_app.config.get("GOOGLE_SERVICE_ACCOUNT_KEY")
        if not raw_key:
            raise DriveNotConfiguredError(
                "GOOGLE_SERVICE_ACCOUNT_KEY ist nicht konfiguriert."
            )

        try:
            decoded = base64.b64decode(raw_key, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise DriveNotConfiguredError(
                "GOOGLE_SERVICE_ACCOUNT_KEY ist kein gueltiges Base64."
            ) from exc

        try:
            info = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise DriveNotConfiguredError(
                "GOOGLE_SERVICE_ACCOUNT_KEY enthaelt kein gueltiges JSON."
            ) from exc

        return service_account.Credentials.from_service_account_info(
            info, scopes=list(DRIVE_SCOPES)
        )

    @classmethod
    def _build_drive(cls):
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise DriveError(
                "google-api-python-client ist nicht installiert."
            ) from exc

        creds = cls._load_credentials()
        # cache_discovery=False vermeidet File-Cache-Warnings
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    # -- Folder-Management --------------------------------------------------

    @classmethod
    def initialize_folder_structure(cls, drive_id: str | None = None) -> dict[str, str]:
        """Legt die acht Top-Level-Folders im Shared Drive an (idempotent).

        Returns: Dict ``folder_name -> drive_folder_id`` fuer alle Aktiv-
        Kategorien plus den Archiv-Folder.
        """
        drive_id = drive_id or cls._get_drive_id()
        drive = cls._build_drive()

        folder_names: list[str] = list(CATEGORY_FOLDER_NAMES.values())
        folder_names.append(ARCHIVE_FOLDER_NAME)

        result: dict[str, str] = {}
        for name in folder_names:
            existing = cls._find_folder_in_drive(drive, name, drive_id)
            if existing:
                result[name] = existing
                logger.info("Drive-Folder bereits vorhanden: %s (%s)", name, existing)
                continue

            created = cls._create_folder(drive, name, drive_id)
            result[name] = created
            logger.info("Drive-Folder angelegt: %s (%s)", name, created)

        return result

    @staticmethod
    @_drive_retry
    def _find_folder_in_drive(drive, folder_name: str, drive_id: str) -> str | None:
        # Drive-Filename-Suche: einfache Anfuehrungszeichen escapen.
        escaped = folder_name.replace("'", "\\'")
        query = (
            f"name = '{escaped}' "
            f"and mimeType = '{GOOGLE_FOLDER_MIME}' "
            f"and trashed = false"
        )
        response = (
            drive.files()
            .list(
                q=query,
                corpora="drive",
                driveId=drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="files(id, name, parents)",
                pageSize=10,
            )
            .execute()
        )
        files = response.get("files", [])
        # Nur Top-Level (Parent = Drive-Root) zaehlt.
        for file in files:
            parents = file.get("parents") or []
            if drive_id in parents:
                return file["id"]
        return None

    @staticmethod
    @_drive_retry
    def _create_folder(drive, folder_name: str, drive_id: str) -> str:
        body = {
            "name": folder_name,
            "mimeType": GOOGLE_FOLDER_MIME,
            "parents": [drive_id],
        }
        created = (
            drive.files()
            .create(body=body, fields="id", supportsAllDrives=True)
            .execute()
        )
        return created["id"]

    @classmethod
    def get_folder_id(cls, folder_name: str) -> str:
        """Loese Folder-Namen zu Drive-Folder-ID auf (mit Lookup-Cache).

        Cache haengt am Drive-ID-Cache-Key. Auf invalidate-Bedarf bewusst
        verzichtet, weil Folder-IDs in Praxis stabil sind. Bei Bedarf:
        ``DriveStorageService.get_folder_id.cache_clear()``.
        """
        drive_id = cls._get_drive_id()
        return cls._cached_folder_id(drive_id, folder_name)

    @staticmethod
    @lru_cache(maxsize=32)
    def _cached_folder_id(drive_id: str, folder_name: str) -> str:
        drive = DriveStorageService._build_drive()
        folder_id = DriveStorageService._find_folder_in_drive(drive, folder_name, drive_id)
        if not folder_id:
            raise DriveError(
                f"Drive-Folder '{folder_name}' existiert nicht. "
                "Setup-Script `scripts/setup_drive.py` ausfuehren."
            )
        return folder_id

    @classmethod
    def folder_id_for_category(cls, category: DocumentCategory) -> str:
        return cls.get_folder_id(CATEGORY_FOLDER_NAMES[category])

    @classmethod
    def archive_folder_id(cls) -> str:
        return cls.get_folder_id(ARCHIVE_FOLDER_NAME)

    # -- Validierung --------------------------------------------------------

    @staticmethod
    def validate_upload(
        size_bytes: int,
        mime_type: str,
        title: str,
    ) -> None:
        """Server-seitige Validierung (Capability Sektion 11.4)."""
        if size_bytes is None or size_bytes <= 0:
            raise DriveValidationError("Datei ist leer.")
        if size_bytes > MAX_FILE_SIZE_BYTES:
            raise DriveValidationError(
                "Datei ist zu gross (Limit: 100 MB)."
            )
        if mime_type not in ALLOWED_MIME_TYPES:
            raise DriveValidationError(
                f"Dateityp «{mime_type}» ist nicht erlaubt."
            )
        cleaned_title = (title or "").strip()
        if not cleaned_title:
            raise DriveValidationError("Titel ist erforderlich.")
        if len(cleaned_title) > MAX_TITLE_LENGTH:
            raise DriveValidationError(
                f"Titel ist zu lang (Limit: {MAX_TITLE_LENGTH} Zeichen)."
            )

    # -- CRUD ---------------------------------------------------------------

    @classmethod
    def upload_document(
        cls,
        file_stream: IO[bytes],
        title: str,
        category: DocumentCategory,
        uploader: Member,
        event_id: int | None = None,
        original_filename: str | None = None,
        mime_type: str | None = None,
    ) -> Document:
        """Lade Datei hoch (Drive zuerst, dann DB; Rollback bei DB-Fehler)."""
        try:
            from googleapiclient.errors import HttpError
            from googleapiclient.http import MediaIoBaseUpload
        except ImportError as exc:
            raise DriveError("google-api-python-client fehlt.") from exc

        payload = file_stream.read() if hasattr(file_stream, "read") else file_stream
        if not isinstance(payload, (bytes, bytearray)):
            raise DriveValidationError("Datei-Inhalt muss als Bytes vorliegen.")
        size_bytes = len(payload)

        effective_mime = mime_type or "application/octet-stream"
        cls.validate_upload(size_bytes, effective_mime, title)

        # SVG-Sanitization Pflicht (Marketing-Use-Case).
        if effective_mime == "image/svg+xml":
            payload = sanitize_svg_bytes(bytes(payload))
            size_bytes = len(payload)

        drive = cls._build_drive()
        folder_id = cls.folder_id_for_category(category)
        extension = (original_filename or "").rsplit(".", 1)[-1] if original_filename and "." in original_filename else None
        sanitized_filename = sanitize_drive_filename(title, extension)
        sanitized_filename = cls._resolve_filename_collision(
            drive, folder_id, sanitized_filename
        )

        media = MediaIoBaseUpload(
            io.BytesIO(payload), mimetype=effective_mime, resumable=False
        )
        body = {
            "name": sanitized_filename,
            "parents": [folder_id],
            "mimeType": effective_mime,
        }

        try:
            drive_response = cls._drive_create_file(drive, body, media)
        except HttpError as exc:
            cls._handle_quota_error(exc, actor=uploader)
            raise

        try:
            document = Document(
                title=title.strip(),
                category=category,
                status=DocumentStatus.ACTIVE,
                drive_file_id=drive_response["id"],
                drive_web_view_link=drive_response.get("webViewLink"),
                mime_type=effective_mime,
                size_bytes=size_bytes,
                event_id=event_id,
                uploader_id=uploader.id if uploader else None,
                last_synced_at=datetime.utcnow(),
            )
            db.session.add(document)
            db.session.commit()
        except Exception:
            db.session.rollback()
            cls._safe_delete_drive_file(drive, drive_response["id"])
            raise

        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_UPLOADED,
            entity="document",
            entity_id=document.id,
            actor_id=uploader.id if uploader else None,
            extra_data={
                "category": category.value,
                "drive_file_id": document.drive_file_id,
                "size_bytes": size_bytes,
            },
        )
        return document

    @staticmethod
    @_drive_retry
    def _drive_create_file(drive, body: dict, media) -> dict:
        return (
            drive.files()
            .create(
                body=body,
                media_body=media,
                fields="id, name, webViewLink, parents, mimeType, size",
                supportsAllDrives=True,
            )
            .execute()
        )

    @staticmethod
    def _safe_delete_drive_file(drive, file_id: str) -> None:
        try:
            drive.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        except Exception as exc:  # noqa: BLE001 – verwaister File ist okay
            logger.warning(
                "Rollback-Drive-Delete fehlgeschlagen (verwaister File: %s): %s",
                file_id,
                exc,
            )

    @classmethod
    def _resolve_filename_collision(
        cls, drive, folder_id: str, filename: str
    ) -> str:
        """Counter-Suffix `(2)`, `(3)` bei Filename-Kollision (Capability 7.4)."""
        if not cls._filename_exists(drive, folder_id, filename):
            return filename

        base, dot, ext = filename.rpartition(".")
        prefix = base if dot else filename
        suffix = f".{ext}" if dot else ""

        for counter in range(2, 100):
            candidate = f"{prefix} ({counter}){suffix}"
            if not cls._filename_exists(drive, folder_id, candidate):
                return candidate

        # Sehr unwahrscheinlicher Fall: Timestamp anhaengen.
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        return f"{prefix} ({stamp}){suffix}"

    @staticmethod
    @_drive_retry
    def _filename_exists(drive, folder_id: str, filename: str) -> bool:
        escaped = filename.replace("'", "\\'")
        query = (
            f"'{folder_id}' in parents "
            f"and name = '{escaped}' "
            f"and trashed = false"
        )
        response = (
            drive.files()
            .list(
                q=query,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                fields="files(id)",
                pageSize=1,
            )
            .execute()
        )
        return bool(response.get("files"))

    @classmethod
    def download_document(cls, document: Document) -> tuple[bytes, str]:
        """Lade Datei-Inhalt aus dem Drive (fuer App-internen Download)."""
        try:
            from googleapiclient.http import MediaIoBaseDownload
        except ImportError as exc:
            raise DriveError("google-api-python-client fehlt.") from exc

        drive = cls._build_drive()
        request = drive.files().get_media(
            fileId=document.drive_file_id, supportsAllDrives=True
        )
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buffer.getvalue(), document.mime_type or "application/octet-stream"

    @classmethod
    def get_web_view_link(cls, document: Document, refresh: bool = False) -> str:
        """Gibt den `webViewLink` zurueck, optional aus Drive nachladen."""
        if document.drive_web_view_link and not refresh:
            return document.drive_web_view_link

        drive = cls._build_drive()
        meta = (
            drive.files()
            .get(
                fileId=document.drive_file_id,
                fields="webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        link = meta.get("webViewLink")
        if link:
            document.drive_web_view_link = link
            db.session.commit()
        return link or ""

    # -- Lifecycle ----------------------------------------------------------

    @classmethod
    def archive_document(cls, document: Document, archived_by: Member) -> None:
        if document.status == DocumentStatus.ARCHIVED:
            return  # idempotent

        cls._move_drive_file(
            document.drive_file_id,
            new_parent_id=cls.archive_folder_id(),
            old_parent_id=cls.folder_id_for_category(document.category),
        )
        document.status = DocumentStatus.ARCHIVED
        document.archived_at = datetime.utcnow()
        document.archived_by_id = archived_by.id if archived_by else None
        document.last_synced_at = datetime.utcnow()
        db.session.commit()

        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_ARCHIVED,
            entity="document",
            entity_id=document.id,
            actor_id=archived_by.id if archived_by else None,
        )

    @classmethod
    def restore_document(cls, document: Document, restored_by: Member) -> None:
        if document.status == DocumentStatus.ACTIVE:
            return

        cls._move_drive_file(
            document.drive_file_id,
            new_parent_id=cls.folder_id_for_category(document.category),
            old_parent_id=cls.archive_folder_id(),
        )
        document.status = DocumentStatus.ACTIVE
        document.archived_at = None
        document.archived_by_id = None
        document.last_synced_at = datetime.utcnow()
        db.session.commit()

        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_RESTORED,
            entity="document",
            entity_id=document.id,
            actor_id=restored_by.id if restored_by else None,
        )

    @classmethod
    def permanently_delete_document(
        cls, document: Document, deleted_by: Member
    ) -> None:
        """Drive-Trash + DB-Hard-Delete; AuditEvent mit Snapshot."""
        snapshot = {
            "id": document.id,
            "title": document.title,
            "category": document.category.value,
            "status": document.status.value,
            "drive_file_id": document.drive_file_id,
            "mime_type": document.mime_type,
            "size_bytes": document.size_bytes,
            "uploader_id": document.uploader_id,
            "created_at": document.created_at.isoformat()
            if document.created_at
            else None,
        }

        drive = cls._build_drive()
        try:
            drive.files().update(
                fileId=document.drive_file_id,
                body={"trashed": True},
                supportsAllDrives=True,
            ).execute()
        except Exception as exc:
            logger.error(
                "Drive-Trash fehlgeschlagen fuer document %s: %s",
                document.id,
                exc,
            )
            # Wir loeschen den DB-Record nicht ohne Drive-Trash-Erfolg.
            raise

        db.session.delete(document)
        db.session.commit()

        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_PERMANENTLY_DELETED,
            entity="document",
            entity_id=snapshot["id"],
            actor_id=deleted_by.id if deleted_by else None,
            extra_data={"snapshot": snapshot},
        )

    @classmethod
    def change_category(
        cls,
        document: Document,
        new_category: DocumentCategory,
        changed_by: Member,
    ) -> None:
        if document.category == new_category:
            return
        if document.status != DocumentStatus.ACTIVE:
            raise DriveError("Archivierte Dokumente koennen nicht verschoben werden.")

        cls._move_drive_file(
            document.drive_file_id,
            new_parent_id=cls.folder_id_for_category(new_category),
            old_parent_id=cls.folder_id_for_category(document.category),
        )
        old_category = document.category
        document.category = new_category
        document.last_synced_at = datetime.utcnow()
        db.session.commit()

        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_MOVED,
            entity="document",
            entity_id=document.id,
            actor_id=changed_by.id if changed_by else None,
            extra_data={
                "from": old_category.value,
                "to": new_category.value,
            },
        )

    @classmethod
    def rename_document(
        cls, document: Document, new_title: str, renamed_by: Member
    ) -> None:
        new_title = (new_title or "").strip()
        if not new_title:
            raise DriveValidationError("Titel ist erforderlich.")
        if len(new_title) > MAX_TITLE_LENGTH:
            raise DriveValidationError(
                f"Titel ist zu lang (Limit: {MAX_TITLE_LENGTH} Zeichen)."
            )

        drive = cls._build_drive()
        # Aktuelle Extension aus dem Drive-File ableiten, damit die Drive-
        # Suche/Sortierung weiterhin sauber funktioniert.
        existing = (
            drive.files()
            .get(
                fileId=document.drive_file_id,
                fields="name",
                supportsAllDrives=True,
            )
            .execute()
        )
        existing_name = existing.get("name") or ""
        ext = existing_name.rsplit(".", 1)[-1] if "." in existing_name else None
        new_filename = sanitize_drive_filename(new_title, ext)

        # Bei Kollision Counter-Suffix anwenden im selben Folder.
        folder_id = (
            cls.archive_folder_id()
            if document.is_archived
            else cls.folder_id_for_category(document.category)
        )
        new_filename = cls._resolve_filename_collision(drive, folder_id, new_filename)

        drive.files().update(
            fileId=document.drive_file_id,
            body={"name": new_filename},
            supportsAllDrives=True,
        ).execute()

        old_title = document.title
        document.title = new_title
        document.last_synced_at = datetime.utcnow()
        db.session.commit()

        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_RENAMED,
            entity="document",
            entity_id=document.id,
            actor_id=renamed_by.id if renamed_by else None,
            extra_data={"from": old_title, "to": new_title},
        )

    @classmethod
    @_drive_retry
    def _move_drive_file(
        cls,
        drive_file_id: str,
        new_parent_id: str,
        old_parent_id: str,
    ) -> None:
        drive = cls._build_drive()
        drive.files().update(
            fileId=drive_file_id,
            addParents=new_parent_id,
            removeParents=old_parent_id,
            fields="id, parents",
            supportsAllDrives=True,
        ).execute()

    # -- Listing / Query (DB-only) -----------------------------------------

    @staticmethod
    def list_documents(
        category: DocumentCategory | None = None,
        status: DocumentStatus = DocumentStatus.ACTIVE,
        search: str | None = None,
    ) -> list[Document]:
        query = Document.query.filter(Document.status == status)
        if category is not None:
            query = query.filter(Document.category == category)
        if search:
            like = f"%{search.strip()}%"
            query = query.filter(Document.title.ilike(like))
        return query.order_by(Document.created_at.desc()).all()

    # -- Sync (Capability Sektion 9) ----------------------------------------

    @classmethod
    def auto_sync_document(cls, document: Document) -> SyncResult:
        """Leichter API-Check beim Detail-View; korrigiert Drift silent."""
        result = SyncResult(document_id=document.id)
        try:
            drive = cls._build_drive()
            meta = (
                drive.files()
                .get(
                    fileId=document.drive_file_id,
                    fields="id, parents, name, trashed",
                    supportsAllDrives=True,
                )
                .execute()
            )
        except Exception as exc:
            from googleapiclient.errors import HttpError

            if isinstance(exc, HttpError) and getattr(exc.resp, "status", None) == 404:
                # File existiert nicht mehr im Drive – DB-Eintrag entfernen.
                snapshot_id = document.id
                db.session.delete(document)
                db.session.commit()
                SecurityService.log_audit_event(
                    AuditAction.DOCUMENT_AUTO_SYNCED,
                    entity="document",
                    entity_id=snapshot_id,
                    extra_data={"reason": "drive_file_missing"},
                )
                result.drift_detected = True
                result.actions.append("removed_orphan_db_entry")
                return result
            logger.warning("auto_sync fuer document %s fehlgeschlagen: %s",
                           document.id, exc)
            result.note = f"sync_failed: {exc}"
            return result

        if meta.get("trashed"):
            snapshot_id = document.id
            db.session.delete(document)
            db.session.commit()
            SecurityService.log_audit_event(
                AuditAction.DOCUMENT_AUTO_SYNCED,
                entity="document",
                entity_id=snapshot_id,
                extra_data={"reason": "drive_file_trashed"},
            )
            result.drift_detected = True
            result.actions.append("removed_trashed_db_entry")
            return result

        parents = meta.get("parents") or []
        archive_id = cls.archive_folder_id()
        active_id = cls.folder_id_for_category(document.category)

        # Drift: Status ARCHIVED, aber File ist im Aktiv-Folder.
        if document.status == DocumentStatus.ARCHIVED and active_id in parents:
            document.status = DocumentStatus.ACTIVE
            document.archived_at = None
            document.archived_by_id = None
            result.drift_detected = True
            result.actions.append("status_active")
        # Drift: Status ACTIVE, aber File ist im Archiv.
        elif document.status == DocumentStatus.ACTIVE and archive_id in parents:
            document.status = DocumentStatus.ARCHIVED
            document.archived_at = datetime.utcnow()
            result.drift_detected = True
            result.actions.append("status_archived")

        document.last_synced_at = datetime.utcnow()
        db.session.commit()
        if result.drift_detected:
            SecurityService.log_audit_event(
                AuditAction.DOCUMENT_AUTO_SYNCED,
                entity="document",
                entity_id=document.id,
                extra_data={"actions": result.actions},
            )
        return result

    @classmethod
    def admin_full_resync(cls, actor: Member | None = None) -> ResyncReport:
        """Vollstaendiger Drift-Abgleich ueber alle acht Folders."""
        report = ResyncReport()
        drive = cls._build_drive()
        drive_id = cls._get_drive_id()

        active_folder_ids: dict[str, tuple[DocumentCategory, str]] = {}
        for cat, folder_name in CATEGORY_FOLDER_NAMES.items():
            folder_id = cls.get_folder_id(folder_name)
            active_folder_ids[folder_id] = (cat, folder_name)

        archive_folder_id = cls.archive_folder_id()

        seen_drive_ids: set[str] = set()

        for folder_id, (category, folder_name) in active_folder_ids.items():
            files = cls._list_files_in_folder(drive, folder_id, drive_id)
            report.folders_seen += 1
            for file in files:
                seen_drive_ids.add(file["id"])
                cls._reconcile_file(file, category, status=DocumentStatus.ACTIVE,
                                     report=report)

        archive_files = cls._list_files_in_folder(drive, archive_folder_id, drive_id)
        report.folders_seen += 1
        for file in archive_files:
            seen_drive_ids.add(file["id"])
            cls._reconcile_file(file, category=None, status=DocumentStatus.ARCHIVED,
                                 report=report)

        # Verwaiste DB-Records: drive_file_id nicht mehr in Drive gefunden.
        orphans = (
            Document.query.filter(~Document.drive_file_id.in_(seen_drive_ids)).all()
        )
        for orphan in orphans:
            db.session.delete(orphan)
            report.orphans_removed += 1
        db.session.commit()

        report.finished_at = datetime.utcnow()
        SecurityService.log_audit_event(
            AuditAction.DRIVE_RESYNC_RAN,
            entity="document",
            actor_id=actor.id if actor else None,
            extra_data={
                "imported": report.imported,
                "moved": report.moved,
                "archived_in_drive": report.archived_in_drive,
                "restored_from_archive": report.restored_from_archive,
                "orphans_removed": report.orphans_removed,
            },
        )
        return report

    @staticmethod
    @_drive_retry
    def _list_files_in_folder(drive, folder_id: str, drive_id: str) -> list[dict]:
        files: list[dict] = []
        page_token: str | None = None
        while True:
            response = (
                drive.files()
                .list(
                    q=(
                        f"'{folder_id}' in parents "
                        f"and trashed = false "
                        f"and mimeType != '{GOOGLE_FOLDER_MIME}'"
                    ),
                    corpora="drive",
                    driveId=drive_id,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields=(
                        "nextPageToken, files(id, name, mimeType, size, "
                        "webViewLink, parents, modifiedTime)"
                    ),
                    pageSize=200,
                    pageToken=page_token,
                )
                .execute()
            )
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return files

    @classmethod
    def _reconcile_file(
        cls,
        file: dict,
        category: DocumentCategory | None,
        status: DocumentStatus,
        report: ResyncReport,
    ) -> None:
        existing = Document.query.filter_by(drive_file_id=file["id"]).one_or_none()
        if existing is None:
            # Neu in Drive aufgetaucht – import als System-Eintrag.
            cat_for_db = category or DocumentCategory.SONSTIGES
            doc = Document(
                title=file.get("name") or "Unbenannt",
                category=cat_for_db,
                status=status,
                drive_file_id=file["id"],
                drive_web_view_link=file.get("webViewLink"),
                mime_type=file.get("mimeType"),
                size_bytes=int(file["size"]) if file.get("size") else None,
                uploader_id=None,
                last_synced_at=datetime.utcnow(),
                archived_at=datetime.utcnow() if status == DocumentStatus.ARCHIVED else None,
            )
            db.session.add(doc)
            report.imported += 1
            return

        actions_taken = False
        if status == DocumentStatus.ACTIVE and category is not None:
            if existing.category != category:
                existing.category = category
                report.moved += 1
                actions_taken = True
            if existing.status != DocumentStatus.ACTIVE:
                existing.status = DocumentStatus.ACTIVE
                existing.archived_at = None
                existing.archived_by_id = None
                report.restored_from_archive += 1
                actions_taken = True
        elif status == DocumentStatus.ARCHIVED:
            if existing.status != DocumentStatus.ARCHIVED:
                existing.status = DocumentStatus.ARCHIVED
                existing.archived_at = existing.archived_at or datetime.utcnow()
                report.archived_in_drive += 1
                actions_taken = True

        existing.last_synced_at = datetime.utcnow()
        if actions_taken:
            db.session.flush()

    # -- Member-Lifecycle ---------------------------------------------------

    @classmethod
    def invite_member_to_drive(cls, member: Member) -> None:
        """Drive-Permission anlegen fuer verifizierte google_email."""
        if not member.google_email or not member.google_email_verified:
            raise DriveError(
                "Mitglied hat keine verifizierte Google-Login-Adresse."
            )

        drive = cls._build_drive()
        drive_id = cls._get_drive_id()
        body = {
            "type": "user",
            "role": "fileOrganizer",  # Content Manager
            "emailAddress": member.google_email,
        }
        try:
            cls._drive_create_permission(drive, drive_id, body)
        except Exception as exc:
            SecurityService.log_audit_event(
                AuditAction.DRIVE_MEMBERSHIP_FAILED,
                entity="member",
                entity_id=member.id,
                actor_id=member.id,
                extra_data={"error": str(exc)[:300]},
            )
            raise

        SecurityService.log_audit_event(
            AuditAction.DRIVE_MEMBERSHIP_ADDED,
            entity="member",
            entity_id=member.id,
            actor_id=member.id,
            extra_data={"google_email": member.google_email},
        )

    @staticmethod
    @_drive_retry
    def _drive_create_permission(drive, drive_id: str, body: dict) -> dict:
        return (
            drive.permissions()
            .create(
                fileId=drive_id,
                body=body,
                supportsAllDrives=True,
                sendNotificationEmail=False,
            )
            .execute()
        )

    @classmethod
    def remove_member_from_drive(cls, member: Member) -> None:
        if not member.google_email:
            return

        drive = cls._build_drive()
        drive_id = cls._get_drive_id()

        permissions = (
            drive.permissions()
            .list(
                fileId=drive_id,
                supportsAllDrives=True,
                fields="permissions(id, emailAddress)",
            )
            .execute()
        )
        target_id: str | None = None
        for perm in permissions.get("permissions", []):
            if (perm.get("emailAddress") or "").lower() == member.google_email.lower():
                target_id = perm.get("id")
                break

        if not target_id:
            return

        drive.permissions().delete(
            fileId=drive_id, permissionId=target_id, supportsAllDrives=True
        ).execute()
        SecurityService.log_audit_event(
            AuditAction.DRIVE_MEMBERSHIP_REMOVED,
            entity="member",
            entity_id=member.id,
            actor_id=member.id,
            extra_data={"google_email": member.google_email},
        )

    # -- Quota-Handling (Capability Sektion 11.5) --------------------------

    @classmethod
    def _handle_quota_error(cls, exc: Exception, actor: Member | None) -> None:
        from googleapiclient.errors import HttpError

        if not isinstance(exc, HttpError):
            return
        try:
            content = json.loads(exc.content.decode("utf-8") if exc.content else "{}")
        except (ValueError, AttributeError):
            content = {}
        reason = ""
        try:
            reason = content["error"]["errors"][0].get("reason", "")
        except (KeyError, IndexError, TypeError):
            pass
        if reason == "storageQuotaExceeded":
            SecurityService.log_audit_event(
                AuditAction.DRIVE_QUOTA_EXCEEDED,
                entity="document",
                actor_id=actor.id if actor else None,
                extra_data={"raw_reason": reason},
            )
            raise DriveQuotaExceededError(
                "Drive-Speicher ist voll. Bitte wende dich an den Vorstand."
            )
