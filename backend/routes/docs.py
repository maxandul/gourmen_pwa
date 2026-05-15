"""Routes fuer Vereinsdokumente – Drive-Browser (Phase 9).

Pfade:
- /docs/                          Root-Tiles + globale Suche
- /docs/folder/<drive_folder_id>  Ordner-Detail
- /docs/file/<doc_id>             Detail / Audit
- /docs/upload, /docs/file/<id>/* Aktionen
- /docs/api/*                     Folder-Picker (JSON)
"""

from __future__ import annotations

import io

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    send_file,
)
from flask_login import current_user, login_required
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError

from backend.extensions import db
from backend.models.audit_event import AuditEvent
from backend.models.document import Document
from backend.models.event import Event
from backend.services.drive_storage import (
    ALLOWED_MIME_TYPES,
    DriveError,
    DriveNotConfiguredError,
    DriveQuotaExceededError,
    DriveStorageService,
    DriveValidationError,
    MAX_FILE_SIZE_BYTES,
)

bp = Blueprint("docs", __name__)


def _drive_enabled() -> bool:
    return bool(current_app.config.get("DRIVE_FEATURE_ENABLED"))


def _require_feature() -> None:
    if not _drive_enabled():
        abort(404)


def _require_admin() -> None:
    if not current_user.is_authenticated or not current_user.is_admin():
        abort(403)


def _validate_csrf_or_403() -> None:
    token = (
        request.form.get("csrf_token")
        or request.headers.get("X-CSRFToken")
        or request.headers.get("X-CSRF-Token")
    )
    try:
        validate_csrf(token)
    except (ValidationError, Exception):
        abort(403)


# ---------------------------------------------------------------------------
# Listing / Folder / Search
# ---------------------------------------------------------------------------


@bp.route("/")
@login_required
def index():
    _require_feature()
    q = (request.args.get("q") or "").strip()
    root_id = DriveStorageService.get_root_id()

    search_hits = []
    if len(q) >= 2:
        try:
            search_hits = DriveStorageService.search_files(q)
        except DriveError as exc:
            current_app.logger.warning("Drive-Suche fehlgeschlagen: %s", exc)
            flash("Suche konnte gerade nicht ausgeführt werden.", "warning")

    top_level = []
    if not search_hits and not q:
        try:
            listing = DriveStorageService.list_folder(root_id)
            top_level = listing.subfolders
        except DriveError as exc:
            current_app.logger.error("Drive-Ordnerliste Root fehlgeschlagen: %s", exc)
            flash("Ordner konnten nicht geladen werden.", "error")

    return render_template(
        "docs/index.html",
        root_folder_id=root_id,
        top_level_folders=top_level,
        search_query=q,
        search_hits=search_hits,
        archive_folder_id=(current_app.config.get("DRIVE_ARCHIVE_FOLDER_ID") or "").strip(),
        max_file_size_mb=MAX_FILE_SIZE_BYTES // (1024 * 1024),
        allowed_mime_types=sorted(ALLOWED_MIME_TYPES),
        events=Event.query.order_by(Event.datum.desc()).limit(50).all(),
    )


@bp.route("/folder/<drive_folder_id>")
@login_required
def folder_view(drive_folder_id: str):
    _require_feature()
    q = (request.args.get("q") or "").strip()
    scope_hits = []
    if len(q) >= 2:
        try:
            scope_hits = DriveStorageService.search_files(q, scope_folder_id=drive_folder_id)
        except DriveError as exc:
            current_app.logger.warning("Drive-Suche Ordner fehlgeschlagen: %s", exc)
            flash("Suche konnte gerade nicht ausgeführt werden.", "warning")

    try:
        listing = DriveStorageService.list_folder(drive_folder_id)
        crumbs = DriveStorageService.get_folder_breadcrumb(drive_folder_id)
    except DriveValidationError:
        abort(404)
    except DriveError as exc:
        current_app.logger.error("Drive-Ordner fehlgeschlagen: %s", exc)
        flash("Ordner konnte nicht geladen werden.", "error")
        return redirect(url_for("docs.index"))

    archive_cfg = (current_app.config.get("DRIVE_ARCHIVE_FOLDER_ID") or "").strip()
    folder_drive_link = DriveStorageService.get_web_view_link_for_folder_id(drive_folder_id)

    return render_template(
        "docs/folder.html",
        root_folder_id=DriveStorageService.get_root_id(),
        drive_folder_id=drive_folder_id,
        listing=listing,
        breadcrumbs=crumbs,
        search_query=q,
        search_hits=scope_hits,
        archive_folder_id=archive_cfg,
        folder_drive_link=folder_drive_link,
        max_file_size_mb=MAX_FILE_SIZE_BYTES // (1024 * 1024),
        allowed_mime_types=sorted(ALLOWED_MIME_TYPES),
        events=Event.query.order_by(Event.datum.desc()).limit(50).all(),
        docs_actions_next=url_for(
            "docs.folder_view", drive_folder_id=drive_folder_id
        ),
    )


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------


@bp.route("/file/<int:doc_id>")
@login_required
def detail(doc_id: int):
    _require_feature()
    document = Document.query.get_or_404(doc_id)

    sync_failed = False
    try:
        DriveStorageService.auto_sync_document(
            document, acting_member=current_user
        )
    except Exception as exc:  # noqa: BLE001
        current_app.logger.warning(
            "auto_sync_document fehlgeschlagen fuer doc %s: %s", doc_id, exc
        )
        sync_failed = True

    fresh = Document.query.get(doc_id)
    if fresh is None:
        flash(
            "Das Dokument wurde direkt im Drive entfernt und ist nicht mehr verfügbar.",
            "warning",
        )
        return redirect(url_for("docs.index"))

    drive_filename = DriveStorageService.fetch_drive_filename(fresh)
    crumbs = DriveStorageService.get_folder_breadcrumb(fresh.drive_parent_id)
    drive_web_link = DriveStorageService.get_web_view_link(fresh)

    history = (
        AuditEvent.query.filter_by(entity="document", entity_id=fresh.id)
        .order_by(AuditEvent.at.desc())
        .limit(10)
        .all()
    )

    in_archive = DriveStorageService.document_is_under_archive(fresh)

    return render_template(
        "docs/detail.html",
        document=fresh,
        drive_filename=drive_filename,
        drive_web_link=drive_web_link,
        breadcrumbs=crumbs,
        history=history,
        sync_failed=sync_failed,
        in_archive=in_archive,
        events=Event.query.order_by(Event.datum.desc()).limit(50).all(),
        docs_actions_next=url_for(
            "docs.folder_view", drive_folder_id=fresh.drive_parent_id
        ),
    )
# ---------------------------------------------------------------------------


@bp.route("/api/root", methods=["GET"])
@login_required
def api_root():
    _require_feature()
    rid = DriveStorageService.get_root_id()
    return jsonify({"id": rid, "name": "Dokumente"})


@bp.route("/api/folder/<drive_folder_id>/children", methods=["GET"])
@login_required
def api_folder_children(drive_folder_id: str):
    _require_feature()
    try:
        subs = DriveStorageService.list_subfolders_only(drive_folder_id)
    except DriveError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(
        {
            "folders": [{"id": f.id, "name": f.name} for f in subs],
        }
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
        flash("Bitte wähle eine Datei aus.", "error")
        return redirect(_redirect_docs_fallback())

    folder_raw = (request.form.get("drive_folder_id") or "").strip()
    if not folder_raw:
        flash("Kein Zielordner gewählt.", "error")
        return redirect(_redirect_docs_fallback())

    title = (request.form.get("title") or "").strip()
    if not title:
        title = upload_file.filename.rsplit(".", 1)[0]

    event_raw = (request.form.get("event_id") or "").strip()
    event_id = int(event_raw) if event_raw.isdigit() else None

    raw_bytes = upload_file.read()
    mime_type = upload_file.mimetype or "application/octet-stream"

    try:
        document = DriveStorageService.upload_document(
            file_stream=io.BytesIO(raw_bytes),
            filename_stem=title,
            drive_folder_id=folder_raw,
            uploader=current_user,
            event_id=event_id,
            original_filename=upload_file.filename,
            mime_type=mime_type,
        )
    except DriveValidationError as exc:
        flash(str(exc), "error")
        return redirect(_redirect_docs_upload(folder_raw))
    except DriveQuotaExceededError as exc:
        flash(str(exc), "error")
        return redirect(_redirect_docs_upload(folder_raw))
    except DriveError as exc:
        current_app.logger.error("Drive-Upload fehlgeschlagen: %s", exc, exc_info=True)
        flash("Drive-Upload fehlgeschlagen. Bitte später erneut versuchen.", "error")
        return redirect(_redirect_docs_upload(folder_raw))

    flash(f"«{DriveStorageService.fetch_drive_filename(document)}» wurde hochgeladen.", "success")
    return redirect(url_for("docs.folder_view", drive_folder_id=folder_raw))


def _redirect_docs_fallback():
    return url_for("docs.index")


def _redirect_docs_upload(folder_id: str | None) -> str:
    if folder_id:
        return url_for("docs.folder_view", drive_folder_id=folder_id)
    return url_for("docs.index")


# ---------------------------------------------------------------------------
# Aktionen
# ---------------------------------------------------------------------------


@bp.route("/file/<int:doc_id>/rename", methods=["POST"])
@login_required
def rename(doc_id: int):
    _require_feature()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)
    next_url = request.form.get("next") or url_for(
        "docs.folder_view", drive_folder_id=document.drive_parent_id
    )
    new_title = (request.form.get("title") or "").strip()
    try:
        DriveStorageService.rename_document(document, new_title, current_user)
    except DriveValidationError as exc:
        flash(str(exc), "error")
        return redirect(next_url)
    except DriveError as exc:
        current_app.logger.error("Drive-Rename fehlgeschlagen: %s", exc, exc_info=True)
        flash("Umbenennen fehlgeschlagen. Bitte später erneut versuchen.", "error")
        return redirect(next_url)

    flash("Datei wurde umbenannt.", "success")
    return redirect(next_url)


@bp.route("/file/<int:doc_id>/move", methods=["POST"])
@login_required
def move(doc_id: int):
    _require_feature()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)
    next_url = request.form.get("next") or url_for(
        "docs.folder_view", drive_folder_id=document.drive_parent_id
    )
    parent_raw = (request.form.get("new_parent_id") or "").strip()
    if not parent_raw:
        flash("Kein Zielordner gewählt.", "error")
        return redirect(next_url)
    try:
        DriveStorageService.move_document(document, parent_raw, current_user)
    except DriveValidationError as exc:
        flash(str(exc), "error")
        return redirect(next_url)
    except DriveError as exc:
        current_app.logger.error("Drive-Move fehlgeschlagen: %s", exc, exc_info=True)
        flash("Verschieben fehlgeschlagen. Bitte später erneut versuchen.", "error")
        return redirect(next_url)

    flash("Datei wurde verschoben.", "success")
    return redirect(next_url)


@bp.route("/file/<int:doc_id>/archive", methods=["POST"])
@login_required
def archive(doc_id: int):
    _require_feature()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)
    next_url = request.form.get("next") or url_for(
        "docs.folder_view", drive_folder_id=document.drive_parent_id
    )
    try:
        DriveStorageService.archive_document(document, current_user)
    except DriveNotConfiguredError as exc:
        flash(str(exc), "error")
        return redirect(next_url)
    except DriveError as exc:
        current_app.logger.error("Drive-Archive fehlgeschlagen: %s", exc, exc_info=True)
        flash("Archivieren fehlgeschlagen. Bitte später erneut versuchen.", "error")
        return redirect(next_url)

    flash("Datei wurde ins Archiv verschoben.", "success")
    aid = (current_app.config.get("DRIVE_ARCHIVE_FOLDER_ID") or "").strip()
    if aid:
        return redirect(url_for("docs.folder_view", drive_folder_id=aid))
    return redirect(url_for("docs.index"))


@bp.route("/file/<int:doc_id>/restore", methods=["POST"])
@login_required
def restore(doc_id: int):
    _require_feature()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)
    next_url = request.form.get("next") or url_for("docs.detail", doc_id=doc_id)
    target = (request.form.get("target_folder_id") or "").strip()
    if not target:
        flash("Kein Zielordner gewählt.", "error")
        return redirect(next_url)
    try:
        DriveStorageService.restore_document(document, target, current_user)
    except DriveError as exc:
        current_app.logger.error(
            "Drive-Restore fehlgeschlagen: %s", exc, exc_info=True
        )
        flash(str(exc), "error")
        return redirect(next_url)

    flash("Datei wurde wiederhergestellt.", "success")
    return redirect(url_for("docs.folder_view", drive_folder_id=target))


@bp.route("/file/<int:doc_id>/delete", methods=["POST"])
@login_required
def hard_delete(doc_id: int):
    _require_feature()
    _require_admin()
    _validate_csrf_or_403()
    document = Document.query.get_or_404(doc_id)

    if not DriveStorageService.document_is_under_archive(document):
        flash("Endgültig löschen ist nur im Archiv möglich.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    drive_filename = DriveStorageService.fetch_drive_filename(document)
    confirm = (request.form.get("confirm_filename") or "").strip()
    if confirm != drive_filename:
        flash("Bestätigung stimmt nicht mit dem Dateinamen überein.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    try:
        DriveStorageService.permanently_delete_document(document, current_user)
    except DriveError as exc:
        current_app.logger.error(
            "Drive-Hard-Delete fehlgeschlagen: %s", exc, exc_info=True
        )
        flash("Endgültiges Löschen fehlgeschlagen.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    flash(
        f"«{drive_filename}» wurde in den Drive-Papierkorb verschoben (30 Tage Aufbewahrung).",
        "success",
    )
    aid = (current_app.config.get("DRIVE_ARCHIVE_FOLDER_ID") or "").strip()
    if aid:
        return redirect(url_for("docs.folder_view", drive_folder_id=aid))
    return redirect(url_for("docs.index"))


@bp.route("/file/<int:doc_id>/download")
@login_required
def download(doc_id: int):
    _require_feature()
    document = Document.query.get_or_404(doc_id)
    try:
        payload, mime, fname = DriveStorageService.download_document(document)
    except DriveError as exc:
        current_app.logger.error(
            "Drive-Download fehlgeschlagen: %s", exc, exc_info=True
        )
        flash("Download fehlgeschlagen. Bitte später erneut versuchen.", "error")
        return redirect(url_for("docs.detail", doc_id=doc_id))

    return send_file(
        io.BytesIO(payload),
        mimetype=mime,
        as_attachment=True,
        download_name=fname,
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
        flash("Drive-Re-Sync fehlgeschlagen. Bitte Logs prüfen.", "error")
        return redirect(url_for("admin.index"))

    if report.total_changes == 0:
        flash("Drive-Re-Sync fertig: alles war bereits konsistent.", "success")
    else:
        flash(
            "Drive-Re-Sync fertig: "
            f"{report.imported} neu importiert, "
            f"{report.parent_updates} Ordner-Zuordnungen aktualisiert, "
            f"{report.orphans_removed} verwaiste Einträge bereinigt.",
            "success",
        )
    return redirect(url_for("admin.index"))
