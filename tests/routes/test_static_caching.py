"""Regressionstests fuer die Auslieferung statischer Assets.

Hintergrund: Flask lieferte alle Dateien unter /static/ mit
`Cache-Control: no-cache` aus. Bei rund 50 Assets pro Seitenaufruf bedeutete
das 50 Revalidierungen gegen den Server - hinter einem scannenden Firmenproxy
genug, um render-blockierendes CSS ausbremsen oder abreissen zu lassen (Seite
ohne Layout). Gehashte Dateien sind unveraenderlich und duerfen dauerhaft
gecacht werden.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STYLESHEET_PARTIAL = REPO_ROOT / "templates" / "partials" / "_head_stylesheets.html"


def _bundle_href() -> str:
    """Der aktuell im Template referenzierte CSS-Bundle-Pfad."""
    html = STYLESHEET_PARTIAL.read_text(encoding="utf-8")
    match = re.search(r"filename='(css/main-v2\.[0-9a-f]{8}\.css)'", html)
    assert match, "Kein gehashtes CSS-Bundle in _head_stylesheets.html gefunden"
    return "/static/" + match.group(1)


def test_gehashtes_asset_wird_unveraenderlich_gecacht(client):
    resp = client.get(_bundle_href())

    assert resp.status_code == 200
    cache_control = resp.headers["Cache-Control"]
    assert "max-age=31536000" in cache_control
    assert "immutable" in cache_control


def test_ungehashtes_asset_bekommt_kurze_lebensdauer(client):
    resp = client.get("/static/js/v2/theme.js")

    assert resp.status_code == 200
    # Kurz genug, dass ein vergessener Cache-Buster nicht zur Dauerlast wird.
    assert "max-age=3600" in resp.headers["Cache-Control"]


def test_static_ohne_content_disposition(client):
    """`Content-Disposition` bringt fuer Subresourcen nichts, triggert aber die
    Download-Inspektion mancher Security-Gateways."""
    resp = client.get(_bundle_href())

    assert "Content-Disposition" not in resp.headers


def test_service_worker_bleibt_ungecacht(client):
    """sw.js darf NIE lange gecacht werden - sonst kommen SW-Updates nie an."""
    resp = client.get("/sw.js")

    assert resp.status_code == 200
    assert "no-cache" in resp.headers["Cache-Control"]


def test_css_bundle_enthaelt_keine_import_kette(client):
    """Das Bundle muss das Design-System selbst enthalten, nicht nur nachladen.

    Eine @import-Kette zwang den Browser, erst die kleine Huelle zu laden und zu
    parsen, bevor er die eigentlichen Stylesheets anfordern konnte - ein
    render-blockierender Wasserfall, der in langsamen Netzen riss.
    """
    body = client.get(_bundle_href()).get_data(as_text=True)

    assert "@import" not in body
    # Stichproben aus allen vier Quelldateien.
    assert "--color-text-primary" in body   # v2/tokens.css
    assert ".main-content" in body          # v2/layout.css


def test_kein_template_laedt_das_master_logo():
    """static/brand/logo-master-round.svg ist 2.85 MB (eingebettete 1300x1300-
    Bitmap plus C2PA-Metadaten) und wurde frueher auf jeder Seite geladen -
    als Hero-Bild, in der User-Bar und als SVG-Favicon.

    Fuers Web erzeugt scripts/build_web_logo.py schlanke WebP-Varianten.
    Das Master-Asset bleibt die Quelle fuer die Icon-Generierung, gehoert aber
    in kein ausgeliefertes Template.
    """
    offenders = []
    for template in (REPO_ROOT / "templates").rglob("*.html"):
        # HTML-Kommentare raus: dort darf der Dateiname zur Erklaerung stehen.
        markup = re.sub(r"<!--.*?-->", "", template.read_text(encoding="utf-8"), flags=re.S)
        if "logo-master" in markup:
            offenders.append(template.relative_to(REPO_ROOT).as_posix())

    assert not offenders, f"Master-Logo direkt referenziert in: {offenders}"


def test_ausgelieferte_logos_bleiben_klein():
    logos = sorted((REPO_ROOT / "static" / "img" / "brand").glob("logo-round-*.webp"))

    assert logos, "Keine Web-Logos gefunden - scripts/build_web_logo.py ausfuehren"
    for logo in logos:
        kb = logo.stat().st_size / 1024
        assert kb < 100, f"{logo.name} ist {kb:.0f} KB gross"


def test_alle_statischen_referenzen_der_landingpage_aufloesbar(client):
    """Fingerprints werden von Hand in die Templates gepflegt - ein Tippfehler
    faellt sonst erst in Produktion als 404 auf (so geschehen bei
    splash-828x1792, das den Hash von splash-1242x2208 trug)."""
    html = client.get("/").get_data(as_text=True)
    refs = {u.split("#")[0] for u in re.findall(r'(?:href|src)="(/static/[^"]+)"', html)}

    assert refs, "Keine statischen Referenzen gefunden"
    broken = [u for u in sorted(refs) if client.get(u).status_code != 200]

    assert not broken, f"Nicht aufloesbare Static-Referenzen: {broken}"
