"""DriveStorageService – Vereinsdokumente im Google Shared Drive.

Authoritative Spezifikation: docs/capabilities/drive.md (Drive-Browser-Modell).

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
from typing import IO

from flask import current_app
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from backend.extensions import db
from backend.models.audit_event import AuditAction
from backend.models.document import Document
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
    """Validierung gegen MIME-Allowlist, Groessen-Limit, Filename-Regeln."""


class DriveSanitizationError(DriveError):
    """SVG kann nicht sicher sanitiziert werden."""


# ---------------------------------------------------------------------------
# Konstanten (Capability Sektion 11)
# ---------------------------------------------------------------------------


MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB Hard-Limit pro Datei
MAX_FILENAME_STEM_LENGTH = 200

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "application/rtf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/heic",
        "image/heif",
        "image/svg+xml",
        "application/vnd.google-apps.document",
        "application/vnd.google-apps.spreadsheet",
        "application/vnd.google-apps.presentation",
    }
)

GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"

DRIVE_SCOPES = ("https://www.googleapis.com/auth/drive",)


# ---------------------------------------------------------------------------
# Result-Datentypen
# ---------------------------------------------------------------------------


@dataclass
class FolderRef:
    """Ein Ordner-Pfad-Segment (Drive-File-ID + Anzeigename)."""

    id: str
    name: str


@dataclass
class FolderMeta:
    """Subfolder-Kachel in der UI."""

    id: str
    name: str
    direct_child_count: int


@dataclass
class FileRow:
    """Ein nicht-Ordner-Eintrag aus Drive mit optionaler DB-Verknuepfung."""

    drive_file_id: str
    name: str
    mime_type: str | None
    modified_time: datetime | None
    web_view_link: str | None
    document_id: int | None
    uploader_id: int | None
    size_bytes: int | None
    uploader_display: str = "extern via Drive"
    icon_name: str = "file"
    relative_label: str = "–"
    document_under_archive: bool = False


@dataclass
class FolderListing:
    """Inhalt eines Drive-Ordners."""

    folder_id: str
    subfolders: list[FolderMeta]
    files: list[FileRow]


@dataclass
class SearchHit:
    """Treffer aus Drive-Volltextsuche."""

    drive_file_id: str
    name: str
    mime_type: str | None
    parent_id: str | None
    breadcrumb: list[FolderRef]
    web_view_link: str | None = None
    icon_name: str = "file"


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
    orphans_removed: int = 0
    parent_updates: int = 0
    files_seen: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return self.imported + self.orphans_removed + self.parent_updates


# ---------------------------------------------------------------------------
# Filename-Sanitization (Capability Sektion 7.4)
# ---------------------------------------------------------------------------


_ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_MULTI_WHITESPACE = re.compile(r"\s+")


def sanitize_drive_filename(title: str, extension: str | None) -> str:
    """Erzeugt einen Drive-tauglichen Filename aus Titel + Extension."""
    base = title or ""
    base = _ILLEGAL_FILENAME_CHARS.sub("-", base)
    base = _MULTI_WHITESPACE.sub(" ", base).strip()
    base = base[:150].rstrip(". ")
    if not base or not re.search(r"[A-Za-z0-9\u00C0-\u017F]", base):
        base = "Untitled"

    if not extension:
        return base

    ext = extension.lstrip(".").strip()
    return f"{base}.{ext}" if ext else base


def relative_modified_label(modified: datetime | None) -> str:
    """Relative Zeitangabe fuer Listen (UTC, schlanke Heuristik)."""
    if modified is None:
        return "–"
    now = datetime.utcnow()
    delta = now - modified
    if delta.total_seconds() < 60:
        return "gerade eben"
    if delta.total_seconds() < 3600:
        m = int(delta.total_seconds() // 60)
        return f"vor {m} Min."
    if delta.days == 0:
        h = int(delta.total_seconds() // 3600)
        return f"vor {h} Std."
    if delta.days == 1:
        return "gestern"
    if delta.days < 7:
        return f"vor {delta.days} Tagen"
    return modified.strftime("%d.%m.%Y")


def mime_to_lucide_icon(mime: str | None, filename: str) -> str:
    """Lucide-Icon-Name fuer MIME-Gruppe (Capability UX)."""
    if mime == "application/pdf":
        return "file-text"
    if mime in (
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        return "file-text"
    if mime in (
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ):
        return "sheet"
    if mime in (
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ):
        return "presentation"
    if mime and mime.startswith("image/"):
        return "image"
    low = (filename or "").lower()
    if low.endswith(".pdf"):
        return "file-text"
    return "file"


# ---------------------------------------------------------------------------
# SVG-Sanitization (Capability Sektion 11.3)
# ---------------------------------------------------------------------------


_SAFE_SVG_HREF = re.compile(r"^(#|\s*$)")
_SVG_EVENT_HANDLER_ATTR = re.compile(r"^on[a-z]+$", re.IGNORECASE)
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
    """Strippt aktive Inhalte aus einem SVG."""
    try:
        from defusedxml import ElementTree as DefusedET
    except ImportError as exc:  # pragma: no cover - defusedxml ist Pflicht
        raise DriveSanitizationError(
            "defusedxml fehlt. SVG-Sanitization nicht moeglich."
        ) from exc

    import xml.etree.ElementTree as ET

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
# Drive-Helfer
# ---------------------------------------------------------------------------


def _parse_drive_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    s = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        from datetime import timezone as tz

        dt = dt.astimezone(tz.utc).replace(tzinfo=None)
    return dt


def _escape_drive_query_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _is_transient_drive_error(exc: BaseException) -> bool:
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

    return isinstance(exc, (TimeoutError, ConnectionError))


_drive_retry = retry(
    retry=retry_if_exception(_is_transient_drive_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    reraise=True,
)


class DriveStorageService:
    """Service-Layer fuer Google Shared Drive Operations."""

    # -- Auth / Client ------------------------------------------------------

    @staticmethod
    def _get_drive_id() -> str:
        drive_id = current_app.config.get("GOOGLE_DRIVE_ID")
        if not drive_id:
            raise DriveNotConfiguredError("GOOGLE_DRIVE_ID ist nicht konfiguriert.")
        return drive_id

    @classmethod
    def get_root_id(cls) -> str:
        """Shared-Drive-Wurzel (= konfigurierte GOOGLE_DRIVE_ID)."""
        return cls._get_drive_id()

    @staticmethod
    def _archive_folder_id_config() -> str | None:
        raw = (current_app.config.get("DRIVE_ARCHIVE_FOLDER_ID") or "").strip()
        return raw or None

    @classmethod
    def _archive_folder_id_required(cls) -> str:
        aid = cls._archive_folder_id_config()
        if not aid:
            raise DriveNotConfiguredError(
                "DRIVE_ARCHIVE_FOLDER_ID ist nicht gesetzt (Archiv-Folder-ID aus Drive)."
            )
        return aid

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
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    # -- Validierung --------------------------------------------------------

    @staticmethod
    def validate_upload(
        size_bytes: int,
        mime_type: str,
        filename_stem: str,
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
        stem = (filename_stem or "").strip()
        if not stem:
            raise DriveValidationError("Dateiname (Titel) ist erforderlich.")
        if len(stem) > MAX_FILENAME_STEM_LENGTH:
            raise DriveValidationError(
                f"Dateiname ist zu lang (Limit: {MAX_FILENAME_STEM_LENGTH} Zeichen)."
            )

    # -- Listing ------------------------------------------------------------

    @staticmethod
    @_drive_retry
    def _list_children_paged(drive, parent_id: str, drive_id: str) -> list[dict]:
        out: list[dict] = []
        page_token: str | None = None
        q_parent = _escape_drive_query_literal(parent_id)
        while True:
            response = (
                drive.files()
                .list(
                    q=f"'{q_parent}' in parents and trashed = false",
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
            out.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return out

    @classmethod
    @_drive_retry
    def _count_direct_children(cls, drive, folder_id: str, drive_id: str) -> int:
        q_parent = _escape_drive_query_literal(folder_id)
        count = 0
        page_token: str | None = None
        while True:
            response = (
                drive.files()
                .list(
                    q=f"'{q_parent}' in parents and trashed = false",
                    corpora="drive",
                    driveId=drive_id,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields="nextPageToken, files(id)",
                    pageSize=1000,
                    pageToken=page_token,
                )
                .execute()
            )
            count += len(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return count

    @classmethod
    def list_folder(cls, drive_folder_id: str) -> FolderListing:
        """Listet direkte Children eines Drive-Ordners."""
        drive = cls._build_drive()
        drive_id = cls._get_drive_id()
        raw = cls._list_children_paged(drive, drive_folder_id, drive_id)

        docs_by_drive_id = {}
        file_items = [it for it in raw if it.get("mimeType") != GOOGLE_FOLDER_MIME]
        if file_items:
            ids = [it["id"] for it in file_items]
            for doc in Document.query.filter(Document.drive_file_id.in_(ids)).all():
                docs_by_drive_id[doc.drive_file_id] = doc

        subfolders: list[FolderMeta] = []
        files: list[FileRow] = []
        archive_id = cls._archive_folder_id_config()

        for item in raw:
            mt = item.get("mimeType")
            if mt == GOOGLE_FOLDER_MIME:
                cid = item["id"]
                cnt = cls._count_direct_children(drive, cid, drive_id)
                subfolders.append(
                    FolderMeta(id=cid, name=item.get("name") or "Ordner", direct_child_count=cnt)
                )
            else:
                doc = docs_by_drive_id.get(item["id"])
                u_disp = "extern via Drive"
                uid = None
                did = None
                if doc:
                    did = doc.id
                    uid = doc.uploader_id
                    if doc.uploader:
                        u_disp = doc.uploader.display_name
                    elif doc.uploader_id:
                        u_disp = "Mitglied"
                    else:
                        u_disp = "extern via Drive"
                under_arch = bool(doc and cls.document_is_under_archive(doc))
                files.append(
                    FileRow(
                        drive_file_id=item["id"],
                        name=item.get("name") or "Unbenannt",
                        mime_type=item.get("mimeType"),
                        modified_time=_parse_drive_time(item.get("modifiedTime")),
                        web_view_link=item.get("webViewLink"),
                        document_id=did,
                        uploader_id=uid,
                        uploader_display=u_disp,
                        size_bytes=int(item["size"]) if item.get("size") else None,
                        icon_name=mime_to_lucide_icon(
                            item.get("mimeType"), item.get("name") or ""
                        ),
                        relative_label=relative_modified_label(
                            _parse_drive_time(item.get("modifiedTime"))
                        ),
                        document_under_archive=under_arch,
                    )
                )

        def folder_sort_key(fm: FolderMeta) -> tuple[int, str]:
            last = 1 if archive_id and fm.id == archive_id else 0
            return (last, fm.name.lower())

        subfolders.sort(key=folder_sort_key)
        files.sort(key=lambda fr: (fr.name or "").lower())

        return FolderListing(
            folder_id=drive_folder_id, subfolders=subfolders, files=files
        )

    @classmethod
    @_drive_retry
    def get_folder_breadcrumb(cls, drive_folder_id: str) -> list[FolderRef]:
        """Pfad vom Shared-Drive-Root bis zum Ordner (ohne synthetisches Root-Label)."""
        drive = cls._build_drive()
        root_id = cls._get_drive_id()
        chain: list[FolderRef] = []
        fid: str | None = drive_folder_id
        safety = 0
        while fid and fid != root_id and safety < 80:
            safety += 1
            meta = (
                drive.files()
                .get(
                    fileId=fid,
                    fields="id, name, parents",
                    supportsAllDrives=True,
                )
                .execute()
            )
            chain.append(
                FolderRef(id=meta["id"], name=meta.get("name") or "Ordner")
            )
            parents = meta.get("parents") or []
            fid = parents[0] if parents else None
        chain.reverse()
        return chain

    @classmethod
    def search_files(
        cls, query: str, scope_folder_id: str | None = None
    ) -> list[SearchHit]:
        """Drive-Volltextsuche; optional auf Unterbaeume gefiltert."""
        q = (query or "").strip()
        if len(q) < 2:
            return []

        drive = cls._build_drive()
        drive_id = cls._get_drive_id()
        escaped = _escape_drive_query_literal(q)
        q_str = (
            f"fullText contains '{escaped}' and trashed = false "
            f"and mimeType != '{GOOGLE_FOLDER_MIME}'"
        )

        hits_raw: list[dict] = []
        page_token: str | None = None
        while True:
            response = (
                drive.files()
                .list(
                    q=q_str,
                    corpora="drive",
                    driveId=drive_id,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields=(
                        "nextPageToken, files(id, name, mimeType, parents, webViewLink)"
                    ),
                    pageSize=50,
                    pageToken=page_token,
                )
                .execute()
            )
            hits_raw.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token or len(hits_raw) >= 50:
                break

        results: list[SearchHit] = []
        for item in hits_raw[:50]:
            parents = item.get("parents") or []
            parent_id = parents[0] if parents else None
            crumbs = cls.get_folder_breadcrumb(parent_id) if parent_id else []
            if scope_folder_id:
                if parent_id != scope_folder_id and not cls._path_contains_folder(
                    crumbs, scope_folder_id
                ):
                    continue
            results.append(
                SearchHit(
                    drive_file_id=item["id"],
                    name=item.get("name") or "Unbenannt",
                    mime_type=item.get("mimeType"),
                    parent_id=parent_id,
                    breadcrumb=crumbs,
                    web_view_link=item.get("webViewLink"),
                    icon_name=mime_to_lucide_icon(
                        item.get("mimeType"), item.get("name") or ""
                    ),
                )
            )
        return results

    @staticmethod
    def _path_contains_folder(crumbs: list[FolderRef], folder_id: str) -> bool:
        return any(seg.id == folder_id for seg in crumbs)

    @classmethod
    def list_subfolders_only(cls, drive_folder_id: str) -> list[FolderRef]:
        """Nur direkte Unterordner (Folder-Picker / API)."""
        listing = cls.list_folder(drive_folder_id)
        return [FolderRef(id=f.id, name=f.name) for f in listing.subfolders]

    # -- Ordner-Validierung -------------------------------------------------

    @classmethod
    @_drive_retry
    def assert_is_folder_in_drive(cls, drive_folder_id: str) -> None:
        drive = cls._build_drive()
        drive_id = cls._get_drive_id()
        meta = (
            drive.files()
            .get(
                fileId=drive_folder_id,
                fields="id, mimeType, parents, trashed",
                supportsAllDrives=True,
            )
            .execute()
        )
        if meta.get("trashed"):
            raise DriveValidationError("Zielordner ist nicht verfuegbar.")
        if meta.get("mimeType") != GOOGLE_FOLDER_MIME:
            raise DriveValidationError("Ziel ist kein Ordner.")
        parents = meta.get("parents") or []
        if drive_id not in parents and drive_folder_id != drive_id:
            # Ordner kann verschachtelt sein: Parent-Kette muss unter dem Drive landen
            if not cls._folder_reachable_from_root(drive, drive_folder_id, drive_id):
                raise DriveValidationError("Ordner liegt nicht im Vereins-Drive.")

    @classmethod
    def _folder_reachable_from_root(cls, drive, folder_id: str, root_id: str) -> bool:
        fid: str | None = folder_id
        seen: set[str] = set()
        while fid and fid not in seen:
            seen.add(fid)
            if fid == root_id:
                return True
            meta = (
                drive.files()
                .get(fileId=fid, fields="parents", supportsAllDrives=True)
                .execute()
            )
            pars = meta.get("parents") or []
            fid = pars[0] if pars else None
        return False

    @classmethod
    def document_is_under_archive(cls, document: Document) -> bool:
        """True wenn die Datei im Archiv-Baum liegt (ID aus ENV)."""
        aid = cls._archive_folder_id_config()
        if not aid:
            return False
        drive = cls._build_drive()
        return cls._folder_has_ancestor(drive, document.drive_parent_id, aid)

    @classmethod
    def _folder_has_ancestor(cls, drive, folder_id: str, ancestor_id: str) -> bool:
        fid: str | None = folder_id
        root_id = cls._get_drive_id()
        seen: set[str] = set()
        while fid and fid not in seen:
            seen.add(fid)
            if fid == ancestor_id:
                return True
            if fid == root_id:
                break
            meta = (
                drive.files()
                .get(fileId=fid, fields="parents", supportsAllDrives=True)
                .execute()
            )
            pars = meta.get("parents") or []
            fid = pars[0] if pars else None
        return False

    # -- CRUD ---------------------------------------------------------------

    @classmethod
    def upload_document(
        cls,
        file_stream: IO[bytes],
        filename_stem: str,
        drive_folder_id: str,
        uploader: Member,
        event_id: int | None = None,
        original_filename: str | None = None,
        mime_type: str | None = None,
    ) -> Document:
        """Laedt nach Drive hoch und legt den Document-Datensatz an."""
        try:
            from googleapiclient.errors import HttpError
            from googleapiclient.http import MediaIoBaseUpload
        except ImportError as exc:
            raise DriveError("google-api-python-client fehlt.") from exc

        cls.assert_is_folder_in_drive(drive_folder_id)

        payload = file_stream.read() if hasattr(file_stream, "read") else file_stream
        if not isinstance(payload, (bytes, bytearray)):
            raise DriveValidationError("Datei-Inhalt muss als Bytes vorliegen.")
        size_bytes = len(payload)

        effective_mime = mime_type or "application/octet-stream"
        cls.validate_upload(size_bytes, effective_mime, filename_stem)

        if effective_mime == "image/svg+xml":
            payload = sanitize_svg_bytes(bytes(payload))
            size_bytes = len(payload)

        drive = cls._build_drive()
        extension = (
            (original_filename or "").rsplit(".", 1)[-1]
            if original_filename and "." in original_filename
            else None
        )
        sanitized_filename = sanitize_drive_filename(filename_stem, extension)
        sanitized_filename = cls._resolve_filename_collision(
            drive, drive_folder_id, sanitized_filename
        )

        media = MediaIoBaseUpload(
            io.BytesIO(payload), mimetype=effective_mime, resumable=False
        )
        body = {
            "name": sanitized_filename,
            "parents": [drive_folder_id],
            "mimeType": effective_mime,
        }

        try:
            drive_response = cls._drive_create_file(drive, body, media)
        except HttpError as exc:
            cls._handle_quota_error(exc, actor=uploader)
            raise

        parents = drive_response.get("parents") or [drive_folder_id]
        parent_id = parents[0]

        try:
            document = Document(
                drive_file_id=drive_response["id"],
                drive_parent_id=parent_id,
                event_id=event_id,
                uploader_id=uploader.id if uploader else None,
                last_seen_at=datetime.utcnow(),
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
                "drive_folder_id": drive_folder_id,
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
        if not cls._filename_exists(drive, folder_id, filename):
            return filename

        base, dot, ext = filename.rpartition(".")
        prefix = base if dot else filename
        suffix = f".{ext}" if dot else ""

        for counter in range(2, 100):
            candidate = f"{prefix} ({counter}){suffix}"
            if not cls._filename_exists(drive, folder_id, candidate):
                return candidate

        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        return f"{prefix} ({stamp}){suffix}"

    @staticmethod
    @_drive_retry
    def _filename_exists(drive, folder_id: str, filename: str) -> bool:
        escaped_folder = _escape_drive_query_literal(folder_id)
        escaped_name = _escape_drive_query_literal(filename)
        query = (
            f"'{escaped_folder}' in parents "
            f"and name = '{escaped_name}' "
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
    @_drive_retry
    def _drive_file_meta(cls, drive, file_id: str) -> dict:
        return (
            drive.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, parents, webViewLink, trashed",
                supportsAllDrives=True,
            )
            .execute()
        )

    @classmethod
    def fetch_drive_filename(cls, document: Document) -> str:
        drive = cls._build_drive()
        meta = cls._drive_file_meta(drive, document.drive_file_id)
        return meta.get("name") or "Unbenannt"

    @classmethod
    def download_document(cls, document: Document) -> tuple[bytes, str, str]:
        """Bytes, MIME, Original-Dateiname aus Drive."""
        try:
            from googleapiclient.http import MediaIoBaseDownload
        except ImportError as exc:
            raise DriveError("google-api-python-client fehlt.") from exc

        drive = cls._build_drive()
        meta = cls._drive_file_meta(drive, document.drive_file_id)
        name = meta.get("name") or "download"
        mime = meta.get("mimeType") or "application/octet-stream"

        request = drive.files().get_media(
            fileId=document.drive_file_id, supportsAllDrives=True
        )
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buffer.getvalue(), mime, name

    @classmethod
    def get_web_view_link(cls, document: Document) -> str:
        drive = cls._build_drive()
        meta = cls._drive_file_meta(drive, document.drive_file_id)
        return meta.get("webViewLink") or ""

    @classmethod
    def get_web_view_link_for_folder_id(cls, folder_id: str) -> str | None:
        """Öffentlicher Ordner-Link in der Drive-Web-UI."""
        try:
            drive = cls._build_drive()
            meta = (
                drive.files()
                .get(
                    fileId=folder_id,
                    fields="webViewLink",
                    supportsAllDrives=True,
                )
                .execute()
            )
            return meta.get("webViewLink")
        except Exception:  # noqa: BLE001 – UI-Helfer
            return None

    # -- Lifecycle ----------------------------------------------------------

    @classmethod
    def move_document(
        cls,
        document: Document,
        new_parent_id: str,
        moved_by: Member,
        *,
        audit_move: bool = True,
    ) -> None:
        cls.assert_is_folder_in_drive(new_parent_id)
        drive = cls._build_drive()
        meta = cls._drive_file_meta(drive, document.drive_file_id)
        parents = meta.get("parents") or []
        old_parent_id = parents[0] if parents else document.drive_parent_id
        if old_parent_id == new_parent_id:
            return
        cls._move_drive_file(
            document.drive_file_id, new_parent_id, old_parent_id
        )
        document.drive_parent_id = new_parent_id
        document.last_seen_at = datetime.utcnow()
        db.session.commit()

        if audit_move:
            SecurityService.log_audit_event(
                AuditAction.DOCUMENT_MOVED,
                entity="document",
                entity_id=document.id,
                actor_id=moved_by.id if moved_by else None,
                extra_data={
                    "from_folder_id": old_parent_id,
                    "to_folder_id": new_parent_id,
                },
            )

    @classmethod
    def archive_document(cls, document: Document, archived_by: Member) -> None:
        archive_id = cls._archive_folder_id_required()
        if cls.document_is_under_archive(document):
            return
        from_folder_id = document.drive_parent_id
        cls.move_document(
            document,
            archive_id,
            archived_by,
            audit_move=False,
        )
        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_ARCHIVED,
            entity="document",
            entity_id=document.id,
            actor_id=archived_by.id if archived_by else None,
            extra_data={
                "from_folder_id": from_folder_id,
                "archive_folder_id": archive_id,
            },
        )

    @classmethod
    def restore_document(
        cls,
        document: Document,
        target_folder_id: str,
        restored_by: Member,
    ) -> None:
        cls.assert_is_folder_in_drive(target_folder_id)
        archive_id = cls._archive_folder_id_required()
        if not cls.document_is_under_archive(document):
            raise DriveError(
                "Wiederherstellen ist nur fuer Dokumente im Archiv-Baum moeglich."
            )
        cls.move_document(
            document,
            target_folder_id,
            restored_by,
            audit_move=False,
        )
        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_RESTORED,
            entity="document",
            entity_id=document.id,
            actor_id=restored_by.id if restored_by else None,
            extra_data={
                "from_archive_folder_id": archive_id,
                "to_folder_id": target_folder_id,
            },
        )

    @classmethod
    def permanently_delete_document(
        cls, document: Document, deleted_by: Member
    ) -> None:
        drive = cls._build_drive()
        drive_name = cls.fetch_drive_filename(document)
        snapshot = {
            "id": document.id,
            "drive_filename": drive_name,
            "drive_file_id": document.drive_file_id,
            "drive_parent_id": document.drive_parent_id,
            "uploader_id": document.uploader_id,
            "created_at": document.created_at.isoformat()
            if document.created_at
            else None,
        }

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
    def rename_document(
        cls,
        document: Document,
        new_filename_stem: str,
        renamed_by: Member,
    ) -> None:
        stem = (new_filename_stem or "").strip()
        if not stem:
            raise DriveValidationError("Dateiname ist erforderlich.")
        if len(stem) > MAX_FILENAME_STEM_LENGTH:
            raise DriveValidationError(
                f"Dateiname ist zu lang (Limit: {MAX_FILENAME_STEM_LENGTH} Zeichen)."
            )

        drive = cls._build_drive()
        existing = cls._drive_file_meta(drive, document.drive_file_id)
        old_name = existing.get("name") or ""
        ext = old_name.rsplit(".", 1)[-1] if "." in old_name else None
        new_filename = sanitize_drive_filename(stem, ext)

        folder_id = existing.get("parents", [document.drive_parent_id])[0]
        new_filename = cls._resolve_filename_collision(drive, folder_id, new_filename)

        drive.files().update(
            fileId=document.drive_file_id,
            body={"name": new_filename},
            supportsAllDrives=True,
        ).execute()

        document.last_seen_at = datetime.utcnow()
        db.session.commit()

        SecurityService.log_audit_event(
            AuditAction.DOCUMENT_RENAMED,
            entity="document",
            entity_id=document.id,
            actor_id=renamed_by.id if renamed_by else None,
            extra_data={"from": old_name, "to": new_filename},
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

    # -- Sync ---------------------------------------------------------------

    @classmethod
    def auto_sync_document(
        cls, document: Document, *, acting_member: Member
    ) -> SyncResult:
        """Detail-View: Drive pruefen, Parent-Drift korrigieren, Trash/Missing."""
        result = SyncResult(document_id=document.id)
        try:
            drive = cls._build_drive()
            meta = cls._drive_file_meta(drive, document.drive_file_id)
        except Exception as exc:
            from googleapiclient.errors import HttpError

            if isinstance(exc, HttpError) and getattr(exc.resp, "status", None) == 404:
                snapshot_id = document.id
                db.session.delete(document)
                db.session.commit()
                SecurityService.log_audit_event(
                    AuditAction.DOCUMENT_AUTO_REMOVED,
                    entity="document",
                    entity_id=snapshot_id,
                    actor_id=acting_member.id,
                    extra_data={"reason": "drive_file_missing"},
                )
                result.drift_detected = True
                result.actions.append("removed_orphan_db_entry")
                return result
            logger.warning(
                "auto_sync fuer document %s fehlgeschlagen: %s", document.id, exc
            )
            result.note = f"sync_failed: {exc}"
            return result

        if meta.get("trashed"):
            snapshot_id = document.id
            db.session.delete(document)
            db.session.commit()
            SecurityService.log_audit_event(
                AuditAction.DOCUMENT_AUTO_REMOVED,
                entity="document",
                entity_id=snapshot_id,
                actor_id=acting_member.id,
                extra_data={"reason": "drive_file_trashed"},
            )
            result.drift_detected = True
            result.actions.append("removed_trashed_db_entry")
            return result

        parents = meta.get("parents") or []
        actual_parent = parents[0] if parents else document.drive_parent_id

        if actual_parent != document.drive_parent_id:
            document.drive_parent_id = actual_parent
            result.drift_detected = True
            result.actions.append("parent_updated")

        document.last_seen_at = datetime.utcnow()
        db.session.commit()

        if result.drift_detected:
            SecurityService.log_audit_event(
                AuditAction.DOCUMENT_AUTO_SYNCED,
                entity="document",
                entity_id=document.id,
                actor_id=acting_member.id,
                extra_data={"actions": result.actions},
            )
        return result

    @classmethod
    def admin_full_resync(cls, actor: Member) -> ResyncReport:
        """Alle Files im Shared Drive mit der DB abgleichen."""
        report = ResyncReport()
        drive = cls._build_drive()
        drive_id = cls._get_drive_id()

        seen_file_ids: set[str] = set()
        page_token: str | None = None

        while True:
            response = (
                drive.files()
                .list(
                    q="trashed = false",
                    corpora="drive",
                    driveId=drive_id,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields="nextPageToken, files(id, mimeType, parents)",
                    pageSize=1000,
                    pageToken=page_token,
                )
                .execute()
            )
            for item in response.get("files", []):
                if item.get("mimeType") == GOOGLE_FOLDER_MIME:
                    continue
                fid = item["id"]
                parents = item.get("parents") or []
                if not parents:
                    continue
                parent_id = parents[0]
                seen_file_ids.add(fid)
                report.files_seen += 1

                existing = Document.query.filter_by(drive_file_id=fid).one_or_none()
                now = datetime.utcnow()
                if existing is None:
                    doc = Document(
                        drive_file_id=fid,
                        drive_parent_id=parent_id,
                        uploader_id=None,
                        last_seen_at=now,
                    )
                    db.session.add(doc)
                    db.session.flush()
                    report.imported += 1
                    SecurityService.log_audit_event(
                        AuditAction.DOCUMENT_AUTO_IMPORTED,
                        entity="document",
                        entity_id=doc.id,
                        actor_id=actor.id,
                        extra_data={"drive_file_id": fid, "drive_parent_id": parent_id},
                    )
                else:
                    if existing.drive_parent_id != parent_id:
                        existing.drive_parent_id = parent_id
                        report.parent_updates += 1
                    existing.last_seen_at = now

            db.session.commit()

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        orphans = Document.query.filter(
            ~Document.drive_file_id.in_(seen_file_ids)
        ).all()
        for orphan in orphans:
            oid = orphan.id
            dfid = orphan.drive_file_id
            db.session.delete(orphan)
            report.orphans_removed += 1
            SecurityService.log_audit_event(
                AuditAction.DOCUMENT_AUTO_REMOVED,
                entity="document",
                entity_id=oid,
                actor_id=actor.id,
                extra_data={
                    "reason": "orphan_after_resync",
                    "drive_file_id": dfid,
                },
            )
        db.session.commit()

        report.finished_at = datetime.utcnow()
        SecurityService.log_audit_event(
            AuditAction.DRIVE_RESYNC_RAN,
            entity="document",
            actor_id=actor.id,
            extra_data={
                "imported": report.imported,
                "parent_updates": report.parent_updates,
                "orphans_removed": report.orphans_removed,
                "files_seen": report.files_seen,
            },
        )
        return report

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
            "role": "fileOrganizer",
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

    # -- Quota-Handling (Capability Sektion 11.5) ---------------------------

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
                actor_id=actor.id,
                extra_data={"raw_reason": reason},
            )
            raise DriveQuotaExceededError(
                "Drive-Speicher ist voll. Bitte wende dich an den Vorstand."
            )