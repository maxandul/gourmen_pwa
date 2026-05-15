"""Smoke-Tests fuer Vereinsdokumente (/docs): Template + DB, kein Google Live-API."""

from unittest.mock import patch

from backend.services.drive_storage import DriveStorageService, FolderListing


def test_docs_index_renders_with_event_dropdown(logged_in_client, app):
    """Liefert 200 und rendert Event-Zeile im Upload-Modal (faengt falsche Event-Feldnamen)."""
    app.config["GOOGLE_DRIVE_ID"] = "test-shared-drive-id"
    empty_listing = FolderListing(
        folder_id="test-shared-drive-id", subfolders=[], files=[]
    )
    with patch.object(
        DriveStorageService, "list_folder", return_value=empty_listing
    ), patch.object(DriveStorageService, "search_files", return_value=[]):
        resp = logged_in_client.get("/docs/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'id="docs-browser-toolbar"' in html
    assert "Suchen &amp; Hochladen" in html
    assert "docs-browser" in html
    assert "Dokumente</h1>" in html
    assert "Cafe RueTest" in html
