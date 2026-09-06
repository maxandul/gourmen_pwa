"""Regressionstests fuer das Lucide-Icon-Sprite.

Hintergrund: ausgeliefert wird nicht mehr das komplette lucide-static-Sprite
(1666 Symbole, 418 KB), sondern ein von `scripts/build_icon_sprite.py` gebautes
Subset der tatsaechlich referenzierten Icons (~130 Symbole, ~29 KB).

Damit haengt die Sichtbarkeit jedes Icons daran, dass das Subset zu den
Templates passt. Faellt ein Symbol raus - weil jemand ein neues Icon benutzt und
das Script nicht neu laufen laesst, oder weil ein Name sich vertippt hat -, dann
rendert `<use href="...#name">` still gar nichts. Kein 404, keine Konsolen-
Meldung, nur eine leere Flaeche. Genau das faengt dieser Test ab.

Der Test prueft bewusst gegen die Datei, die der Server tatsaechlich ausliefert,
nicht gegen die Quelle auf der Platte.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_icon_sprite.py"
ICON_MACRO = REPO_ROOT / "templates" / "partials" / "_lucide_icon.html"

# Dateien, die auf das Sprite zeigen duerfen. Fingerprint-Kopien sind Duplikate
# ihrer Quelle und tragen zwangslaeufig alte Namen.
_FINGERPRINTED = re.compile(r"\.[0-9a-f]{8}\.[a-z]+$")
_SPRITE_REF = re.compile(r"lucide-sprite(?:-full)?(?:\.[0-9a-f]{8})?\.svg")
_HASHED_SPRITE = re.compile(r"icons/(lucide-sprite\.[0-9a-f]{8}\.svg)")


def _load_build_script():
    """Das Build-Script als Modul - so bleibt die Sammel-Logik single source."""
    spec = importlib.util.spec_from_file_location("build_icon_sprite", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # @dataclass schlaegt im Modul nach, muss also vor exec_module registriert sein.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


build = _load_build_script()


def _referenced_sprite_name() -> str:
    """Der Sprite-Dateiname, den das gemeinsame Icon-Makro referenziert."""
    match = _HASHED_SPRITE.search(ICON_MACRO.read_text(encoding="utf-8"))
    assert match, f"Kein gehashtes Sprite in {ICON_MACRO.name} gefunden"
    return match.group(1)


def _files_referencing_sprite() -> list[Path]:
    candidates = [
        *(REPO_ROOT / "templates").rglob("*.html"),
        *(REPO_ROOT / "static").rglob("*.js"),
        REPO_ROOT / "static" / "offline.html",
    ]
    return [
        path
        for path in sorted(set(candidates))
        if not _FINGERPRINTED.search(path.name)
        and _SPRITE_REF.search(path.read_text(encoding="utf-8"))
    ]


@pytest.fixture
def shipped_symbols(client) -> set[str]:
    """Die Symbol-IDs aus dem Sprite, das der Server wirklich ausliefert."""
    resp = client.get(f"/static/icons/{_referenced_sprite_name()}")
    assert resp.status_code == 200, "Das referenzierte Sprite wird nicht ausgeliefert"
    return set(build.parse_symbols(resp.get_data(as_text=True)))


def test_jedes_referenzierte_symbol_ist_im_ausgelieferten_sprite(shipped_symbols):
    """Der eigentliche Punkt: kein Icon rendert als leere Flaeche."""
    refs = build.collect_icon_refs()
    assert refs, "Keine Icon-Referenzen gefunden - die Sammel-Logik greift nicht mehr"

    fehlend: dict[str, set[str]] = {}
    for ref in refs:
        if ref.name not in shipped_symbols:
            fehlend.setdefault(ref.name, set()).add(ref.origin)

    details = "\n".join(
        f"  #{name}: {', '.join(sorted(origins))}"
        for name, origins in sorted(fehlend.items())
    )
    assert not fehlend, (
        "Symbole fehlen im Sprite - scripts/build_icon_sprite.py neu laufen "
        f"lassen:\n{details}"
    )


def test_alle_referenzen_zeigen_auf_dieselbe_sprite_datei():
    """Zwei URLs fuer dasselbe Sprite bedeuten zwei Downloads (siehe docs/SEO.md)."""
    erwartet = _referenced_sprite_name()
    abweichend: dict[str, set[str]] = {}

    for path in _files_referencing_sprite():
        for name in set(_SPRITE_REF.findall(path.read_text(encoding="utf-8"))):
            if name != erwartet:
                abweichend.setdefault(name, set()).add(
                    str(path.relative_to(REPO_ROOT)).replace("\\", "/")
                )

    assert not abweichend, f"Erwartet wird ueberall {erwartet}, gefunden:\n" + "\n".join(
        f"  {name}: {', '.join(sorted(files))}" for name, files in sorted(abweichend.items())
    )


def test_ausgeliefert_wird_ein_subset_nicht_das_volle_sprite(shipped_symbols):
    """Schuetzt davor, dass das volle Sprite versehentlich zurueckkehrt."""
    voll = build.parse_symbols(build.FULL_SPRITE.read_text(encoding="utf-8"))

    assert len(shipped_symbols) < len(voll) // 5, (
        f"{len(shipped_symbols)} von {len(voll)} Symbolen ausgeliefert - "
        "das sieht nicht mehr nach einem Subset aus"
    )
    assert shipped_symbols <= set(voll), (
        "Das Subset enthaelt Symbole, die es im vollen Sprite nicht gibt"
    )


def test_build_meldet_unbekannte_symbolnamen():
    """Ein Tippfehler im Icon-Namen muss den Build stoppen, nicht Produktion."""
    with pytest.raises(SystemExit) as excinfo:
        build._report_missing({"gibt-es-nicht": ["templates/irgendwo.html:1"]})

    meldung = str(excinfo.value)
    assert "gibt-es-nicht" in meldung
    assert "templates/irgendwo.html:1" in meldung


def test_build_meldet_unaufloesbare_icon_ausdruecke():
    """Eine neue dynamische Icon-Quelle darf nicht still im Subset fehlen."""
    schnipsel = "{{ lucide_icon(irgendein.neues_feld) }}"

    with pytest.raises(SystemExit) as excinfo:
        build._collect_calls(
            ICON_MACRO, schnipsel, "lucide_icon", 0, jinja_literals={}
        )

    assert "irgendein.neues_feld" in str(excinfo.value)
    assert "ALLOWED_DYNAMIC_ARGS" in str(excinfo.value)
