"""Regressionstests fuer die Auffindbarkeit der oeffentlichen Seiten.

Hintergrund: robots.txt und sitemap.xml lieferten 404, es gab keine
Canonical-URLs, und die Meta-Description beschrieb die App statt den Verein
("Gourmen-Verein Webapp - Verwaltung und Organisation"). Die Site war
entsprechend nicht bei Google zu finden. Diese Tests halten den Zustand fest,
damit die Meta-Daten nicht bei der naechsten Template-Umbaute wieder wegfallen.
"""

from __future__ import annotations

import json
import re

import pytest

BASE = "https://www.gourmen.ch"

PUBLIC_PAGES = [
    ("/", f"{BASE}/"),
    ("/ueber-uns", f"{BASE}/ueber-uns"),
    ("/restaurants", f"{BASE}/restaurants"),
]


def _meta(html: str, name: str) -> str | None:
    m = re.search(rf'<meta name="{name}" content="([^"]*)"', html)
    return m.group(1) if m else None


def _canonical(html: str) -> str | None:
    m = re.search(r'<link rel="canonical" href="([^"]*)"', html)
    return m.group(1) if m else None


def test_robots_txt_verweist_auf_sitemap(client):
    resp = client.get("/robots.txt", base_url=BASE)

    assert resp.status_code == 200
    assert "text/plain" in resp.headers["Content-Type"]

    body = resp.get_data(as_text=True)
    assert f"Sitemap: {BASE}/sitemap.xml" in body
    # Interne Bereiche gehoeren nicht in den Index.
    assert "Disallow: /admin/" in body
    assert "Disallow: /dashboard/" in body


def test_sitemap_listet_die_oeffentlichen_seiten(client):
    resp = client.get("/sitemap.xml", base_url=BASE)

    assert resp.status_code == 200
    assert "application/xml" in resp.headers["Content-Type"]

    xml = resp.get_data(as_text=True)
    for _, expected_url in PUBLIC_PAGES:
        assert f"<loc>{expected_url}</loc>" in xml

    # Nichts aus dem Vereinsbereich darf hier auftauchen.
    assert "/dashboard" not in xml
    assert "/admin" not in xml


@pytest.mark.parametrize("path,expected_canonical", PUBLIC_PAGES)
def test_oeffentliche_seite_hat_canonical_und_ist_indexierbar(client, path, expected_canonical):
    html = client.get(path, base_url=BASE).get_data(as_text=True)

    assert _canonical(html) == expected_canonical
    assert _meta(html, "robots") == "index, follow"


@pytest.mark.parametrize("path,_expected", PUBLIC_PAGES)
def test_oeffentliche_seite_hat_aussagekraeftige_description(client, path, _expected):
    description = _meta(client.get(path, base_url=BASE).get_data(as_text=True), "description")

    assert description, f"{path} hat keine Meta-Description"
    # Google kuerzt bei ~160 Zeichen, unter ~80 ist es kein brauchbares Snippet.
    assert len(description) >= 80, f"{path}: Description zu kurz ({len(description)})"
    # Die alte, interne Formulierung darf nicht zurueckkehren.
    assert "Webapp" not in description
    assert "Zürich" in description


def test_paginierte_hitlist_kanonisiert_auf_sich_selbst(client):
    html = client.get("/restaurants?page=2", base_url=BASE).get_data(as_text=True)

    # Ohne page-Parameter im Canonical wuerde Google Seite 2 als Duplikat von
    # Seite 1 werten und gar nicht erst indexieren.
    assert _canonical(html) == f"{BASE}/restaurants?page=2"


def test_landing_liefert_organization_markup(client):
    html = client.get("/", base_url=BASE).get_data(as_text=True)

    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert match, "Kein JSON-LD auf der Landingpage"

    data = json.loads(match.group(1))
    assert data["@type"] == "Organization"
    assert data["name"] == "Gourmen"
    assert data["url"].startswith(BASE)


def test_interner_bereich_bleibt_aus_dem_index(client):
    html = client.get("/auth/login", base_url=BASE, follow_redirects=True).get_data(as_text=True)

    assert "noindex" in (_meta(html, "robots") or "")


def test_apex_leitet_mit_pfad_und_query_auf_www(client):
    resp = client.get("/restaurants?page=3", base_url="https://gourmen.ch")

    assert resp.status_code == 301
    # Eine Umleitung, die den Pfad verwirft, wirft jeden Deeplink auf die
    # Startseite und laesst die Linkkraft der Unterseiten verpuffen.
    assert resp.headers["Location"] == f"{BASE}/restaurants?page=3"
