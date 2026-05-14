"""Smoke-Tests fuer Vereinsdokumente (/docs): Template + DB, kein Google Live-API."""


def test_docs_index_renders_with_event_dropdown(logged_in_client):
    """Liefert 200 und rendert Event-Zeile im Upload-Modal (faengt falsche Event-Feldnamen)."""
    resp = logged_in_client.get("/docs/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "docs-index-toolbar-disclosure" in html
    assert "Suchen &amp; Hochladen" in html
    assert "tabs tabs--panel" in html
    assert "Dokumente</h1>" in html
    assert "Cafe RueTest" in html
