"""Routes fuer Vereinsdokumente im Google Shared Drive (Phase 03).

UI-Routes-Pfade:
- /docs/                 – Listing (Tabs Aktiv-Folders + Archiv)
- /docs/<id>             – Detail-View
- /docs/upload (POST)    – Upload-Endpoint (Drag-and-Drop / File-Picker)
- /docs/<id>/rename      – Umbenennen
- /docs/<id>/move        – Kategorie aendern (Verschieben)
- /docs/<id>/archive     – Archivieren
- /docs/<id>/restore     – Wiederherstellen
- /docs/<id>/delete      – Endgueltig loeschen (Admin)
- /docs/<id>/download    – App-internen Download-Stream
- /docs/admin/resync     – Drive-Re-Sync (Admin)

Routes-Layer macht: Permission-Checks, Form-/Multipart-Handling, Routing.
Drive-Aufrufe gehen ausschliesslich ueber DriveStorageService.
"""

from __future__ import annotations

import io

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError

from backend.extensions import db
from backend.models.audit_event import AuditEvent
from backend.models.document import (
    CATEGORY_LABELS,
    Document,
    DocumentCategory,
    DocumentStatus,
)
from backend.models.event import Event
from backend.services.drive_storage import (
    ALLOWED_MIME_TYPES,
    DriveError,
    DriveQuotaExceededError,
    DriveStorageService,
    DriveValidationError,
    MAX_FILE_SIZE_BYTES,
)

bp = Blueprint("docs", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _drive_enabled() -> bool:
    return bool(current_app.config.get("DRIVE_FEATURE_ENABLED"))


def _require_feature() -> None:
    if not _drive_enabled():
        abort(404)


def _require_admin() -> None:
    if not current_user.is_authenticated or not current_user.is_admin():
        abort(403)


def _validate_csrf_or_403() -> None:
    """Pruefe CSRF-Token aus Form/Header, sonst 403.

    Wird in JSON-/Multipart-Endpoints ohne FlaskForm gebraucht.
    """
    token = (
        request.form.get("csrf_token")
        or request.headers.get("X-CSRFToken")
        or request.headers.get("X-CSRF-Token")
    )
    try:
        validate_csrf(token)
    except (ValidationError, Exception):
        abort(403)


def _category_from_request(field_name: str = "category") -> DocumentCategory:
    raw = (request.form.get(field_name) or "").strip()
    try:
        return DocumentCategory(raw)
    except ValueError:
        raise DriveValidationError(f"Ungueltige Kategorie «{raw}».")


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


@bp.route("/")
@login_required
def index():
    _require_feature()
    tab = (request.args.get("tab") or "all").strip()
    search = (request.args.get("q") or "").strip() or None

    if tab == "archive":
        status = DocumentStatus.ARCHIVED
        category = None
        active_tab = "archive"
    elif tab == "all":
        status = DocumentStatus.ACTIVE
        category = None
        active_tab = "all"
    else:
        try:
            category = DocumentCategory(tab)
        except ValueError:
            category = None
            active_tab = "all"
            status = DocumentStatus.ACTIVE
        else:
            status = DocumentStatus.ACTIVE
            active_tab = tab

    documents = DriveStorageService.list_documents(
        category=category, status=status, search=search
    )

    return render_template(
        "docs/index.html",
        documents=documents,
        active_tab=active_tab,
        search=search,
        category_labels=CATEGORY_LABELS,
        categories=list(DocumentCategory),
        archive_count=Document.query.filter_by(status=DocumentStatus.ARCHIVED).count(),
        max_file_size_mb=MAX_FILE_SIZE_BYTES // (1024 * 1024),
        allowed_mime_types=sorted(ALLOWED_MIME_TYPES),
        events=Event.query.order_by(Event.datum.desc()).limit(50).all(),
    )


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------


@bp.route("/<int:doc_id>")
@login_required
def detail(doc_id: int):
    _require_feature()
    document = Document.query.get_or_404(doc_id)

    # Auto-Sync: leichter API-Check, korrigiert Drift silent (Capability 9.2).
    sync_failed = False
    try:
        DriveStorageService.auto_sync_document(document)
    except Exception as exc:  # noqa: BLE001 – Detail-View darf nicht crashen
        current_app.logger.warning(
            "auto_sync_document fehlgeschlagen fuer doc %s: %s", doc_id, exc
        )
        sync_failed = True

    # Auto-Sync kann das Document geloescht haben.
    fresh = Document.query.get(doc_id)
    if fresh is None:
        flash(
            "Das Dokument wurde direkt im Drive entfernt und ist nicht mehr verfuegbar.",
            "warning",
        )
        return redirect(url_for("docs.index"))

    history = (
        AuditEvent.query.filter_by(entity="document", entity_id=fresh.id)
        .order_by(AuditEvent.at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "docs/detail.html",
        document=fresh,
        history=history,
        sync_failed=sync_failed,
        category_labels=CATEGORY_LABELS,
        categories=list(DocumentCategory),
        events=Event.query.order_by(Event.datum.desc()).limit(50).all(),
    )


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


@bp.route("/upload", methods=["POST"])
@login_required
def upload():
    _require_feature()
    _validate_csrf_or_403()

    upload_file = request.files.get("file")
    if upload_file is None or not upload_file.filename:
        flash("Bitte waehle eine Datei aus.", "error")
        return redirect(url_for("docs.index"))

    title = (request.form.get("title") or "").strip()
    if not title:
        title = upload_file.filename.rsplit(".", 1)[0]

    event_raw = (request.form.get("event_id") or "").strip()
    event_id = int(event_raw) if event_raw.isdigit() else None

    try:
        category = _category_from_request("category")
    except DriveValidationError as exc:
        flash(str(exc), "error")
        return redirect(url_for("docs.index"))

    raw_bytes = upload_file.read()
    mime_type = upload_file.mimetype or "application/octet-stream"

    try:
        document = DriveStorageService.upload_document(
            file_stream=io.BytesIO(raw_bytes),
            title=title,
            category=category,
            uploader=current_user,
            event_id=event_id,
            original_filename=upload_file.filename,
            mime_type=mime_type,
        )
    except DriveValidationError as exc:
        flash(str(exc), "error")
        return redirect(url_for("docs.index"))
    except DriveQuotaExceededError as exc:
        flash(str(exc), "error")
        return redirect(url_for("docs.index"))
    except DriveError as exc:
        current_app.logger.error("Drive-Upload fehlgeschlagen: %s", exc, exc_info=True)
        flash("Drive-Upload fehlgeschlagen. Bitte spaeter erneut versuchen.", "error")
        return redirect(url_for("docs.index"))

    flash(f"«{document.title}» wurde hochgeladen.", "success")
    return redirect(url_for("docs.detail", doc_id=document.id))


# ---------------------------------------------------------------------------
# Aktionen: Rename, Move, Archive, Restore, Permanently Delete
# ---------------------------------------------------------------------------


@bp.route("/<int:doc_id>/rename", methods=["POST"])
@login_required
def rename(doc_id: int):
    _require_feature()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)
    new_title = (request.form.get("title") or "").strip()
    try:
        DriveStorageService.rename_document(document, new_title, current_user)
    except DriveValidationError as exc:
        flash(str(exc), "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))
    except DriveError as exc:
        current_app.logger.error("Drive-Rename fehlgeschlagen: %s", exc, exc_info=True)
        flash("Umbenennen fehlgeschlagen. Bitte spaeter erneut versuchen.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    flash("Dokument wurde umbenannt.", "success")
    return redirect(url_for("docs.detail", doc_id=doc_id))


@bp.route("/<int:doc_id>/move", methods=["POST"])
@login_required
def move(doc_id: int):
    _require_feature()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)
    try:
        new_category = _category_from_request("category")
        DriveStorageService.change_category(document, new_category, current_user)
    except DriveValidationError as exc:
        flash(str(exc), "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))
    except DriveError as exc:
        current_app.logger.error("Drive-Move fehlgeschlagen: %s", exc, exc_info=True)
        flash("Verschieben fehlgeschlagen. Bitte spaeter erneut versuchen.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    flash("Dokument wurde verschoben.", "success")
    return redirect(url_for("docs.detail", doc_id=doc_id))


@bp.route("/<int:doc_id>/archive", methods=["POST"])
@login_required
def archive(doc_id: int):
    _require_feature()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)
    try:
        DriveStorageService.archive_document(document, current_user)
    except DriveError as exc:
        current_app.logger.error("Drive-Archive fehlgeschlagen: %s", exc, exc_info=True)
        flash("Archivieren fehlgeschlagen. Bitte spaeter erneut versuchen.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    flash("Dokument wurde archiviert.", "success")
    return redirect(url_for("docs.index", tab="archive"))


@bp.route("/<int:doc_id>/restore", methods=["POST"])
@login_required
def restore(doc_id: int):
    _require_feature()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)
    try:
        DriveStorageService.restore_document(document, current_user)
    except DriveError as exc:
        current_app.logger.error(
            "Drive-Restore fehlgeschlagen: %s", exc, exc_info=True
        )
        flash("Wiederherstellen fehlgeschlagen.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    flash("Dokument wurde wiederhergestellt.", "success")
    return redirect(url_for("docs.detail", doc_id=doc_id))


@bp.route("/<int:doc_id>/delete", methods=["POST"])
@login_required
def hard_delete(doc_id: int):
    _require_feature()
    _require_admin()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)

    confirm = (request.form.get("confirm_title") or "").strip()
    if confirm != document.title:
        flash("Bestaetigung stimmt nicht mit dem Titel ueberein.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    title = document.title
    try:
        DriveStorageService.permanently_delete_document(document, current_user)
    except DriveError as exc:
        current_app.logger.error(
            "Drive-Hard-Delete fehlgeschlagen: %s", exc, exc_info=True
        )
        flash("Endgueltiges Loeschen fehlgeschlagen.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    flash(
        f"«{title}» wurde in den Drive-Papierkorb verschoben (30 Tage Aufbewahrung).",
        "success",
    )
    return redirect(url_for("docs.index", tab="archive"))


@bp.route("/<int:doc_id>/download")
@login_required
def download(doc_id: int):
    _require_feature()
    document = Document.query.get_or_404(doc_id)
    try:
        payload, mime = DriveStorageService.download_document(document)
    except DriveError as exc:
        current_app.logger.error("Drive-Download fehlgeschlagen: %s", exc, exc_info=True)
        flash("Download fehlgeschlagen. Bitte spaeter erneut versuchen.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    return send_file(
        io.BytesIO(payload),
        mimetype=mime,
        as_attachment=True,
        download_name=document.title,
    )


# ---------------------------------------------------------------------------
# Admin: Re-Sync
# ---------------------------------------------------------------------------


@bp.route("/admin/resync", methods=["POST"])
@login_required
def admin_resync():
    _require_feature()
    _require_admin()
    _validate_csrf_or_403()

    try:
        report = DriveStorageService.admin_full_resync(actor=current_user)
    except DriveError as exc:
        current_app.logger.error("Drive-Resync fehlgeschlagen: %s", exc, exc_info=True)
        flash("Drive-Re-Sync fehlgeschlagen. Bitte Logs pruefen.", "error")
        return redirect(url_for("admin.index"))

    if report.total_changes == 0:
        flash("Drive-Re-Sync fertig: alles war bereits konsistent.", "success")
    else:
        flash(
            "Drive-Re-Sync fertig: "
            f"{report.imported} neu importiert, "
            f"{report.moved} verschoben, "
            f"{report.archived_in_drive} archiviert, "
            f"{report.restored_from_archive} wiederhergestellt, "
            f"{report.orphans_removed} verwaiste Eintraege bereinigt.",
            "success",
        )
    return redirect(url_for("admin.index"))
