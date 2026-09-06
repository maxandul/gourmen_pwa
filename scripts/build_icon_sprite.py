"""Baut aus dem vollen Lucide-Sprite ein Subset der tatsaechlich benutzten Icons.

Hintergrund: `static/icons/lucide-sprite-full.svg` ist das komplette
lucide-static-Sprite mit 1666 Symbolen (418 KB). Es wurde auf jeder Seite
geladen, obwohl die App rund 120 Icons benutzt - der groesste verbliebene
Einzelposten der Ladekette (siehe docs/SEO.md).

Dieses Script sammelt alle tatsaechlich referenzierten Symbol-Namen, schneidet
die passenden `<symbol>`-Bloecke aus dem vollen Sprite heraus, schreibt sie nach
`static/icons/lucide-sprite.svg`, fingerprintet das Ergebnis und traegt es ins
Asset-Manifest ein.

Die Icon-Namen kommen aus mehreren Quellen - sie alle zu finden ist der
eigentliche Kern des Scripts:

  1. `lucide_icon('name')` in den Templates. Das Makro ist pro Template
     dupliziert, der Aufruf ist aber ueberall gleich.
  2. Literale `<use href="...#name">`-Attribute (auch ueber die
     `{% set _sprite = ... %}`-Variante).
  3. Zweites Argument der `dashboard_intent_tile(href, icon_id, ...)`-Aufrufe.
  4. Jinja-Variablen, die im selben Template aus einem Literal gesetzt werden
     (`{% set flash_icon = 'circle-x' %}`).
  5. `lucideInlineIcon('name')` in static/js - Icons, die JS ins DOM schreibt.
  6. Namen aus Python: die Rueckgabewerte von `mime_to_lucide_icon()` und die
     `icon_name`-Defaults der Dataclasses in
     `backend/services/drive_storage.py`. Diese landen ueber `hit.icon_name` /
     `row.icon_name` in den Docs-Templates.

Das Script bricht in drei Faellen ab, statt ein kaputtes Sprite zu bauen:

  - Ein referenzierter Name existiert im vollen Sprite nicht. Sonst faellt ein
    Tippfehler erst als unsichtbares Icon in Produktion auf.
  - Ein Icon-Argument ist ein Ausdruck, den das Script nicht aufloesen kann und
    der nicht in ALLOWED_DYNAMIC_ARGS steht. Wer eine neue dynamische
    Icon-Quelle einbaut, muss sie hier eintragen - sonst fehlt sie still im
    Subset.
  - `mime_to_lucide_icon()` gibt etwas anderes zurueck als String-Literale.

Aufruf:  python scripts/build_icon_sprite.py

Danach muessen der neue Dateiname in `templates/`, `static/offline.html`,
`static/js/app.js` und `static/sw.js` (Liste `STATIC_ASSETS`) nachgezogen und
`python scripts/update_pwa_version.py <version>` ausgefuehrt werden.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
ICONS = STATIC / "icons"
MANIFEST = STATIC / "asset-manifest.json"

# Das vollstaendige lucide-static-Sprite. Reine Quelle, wird nie ausgeliefert -
# bei einem Lucide-Update diese Datei ersetzen und das Script neu laufen lassen.
FULL_SPRITE = ICONS / "lucide-sprite-full.svg"
# Build-Artefakt. Nicht von Hand bearbeiten.
SUBSET_SPRITE = ICONS / "lucide-sprite.svg"

TEMPLATES = ROOT / "templates"
JS_DIR = STATIC / "js"
# Kopie von templates/offline.html, die der Service Worker offline ausliefert.
# Sie wird von Hand synchron gehalten und kann darum eigene Icons enthalten.
EXTRA_HTML = (STATIC / "offline.html",)
DRIVE_STORAGE = ROOT / "backend" / "services" / "drive_storage.py"

HASH_LEN = 8

# Fingerprint-Kopien (app.6763c8b3.js, offline.b3ed91d6.html, ...) sind
# Duplikate ihrer Quelle und wuerden nur veraltete Namen einschleppen.
FINGERPRINTED = re.compile(r"\.[0-9a-f]{8}\.[a-z]+$")

# Ausdruecke, die als Icon-Argument auftauchen duerfen, ohne dass das Script sie
# an Ort und Stelle aufloest - weil eine andere Quelle sie abdeckt.
ALLOWED_DYNAMIC_ARGS = {
    "symbol_id": "Parameter des lucide_icon-Makros; die Aufrufer werden gescannt",
    "icon_id": "Parameter von dashboard_intent_tile; die Aufrufe werden gescannt",
    "symbolId": "Parameter von lucideInlineIcon(); die Aufrufer werden gescannt",
    "hit.icon_name": "aus drive_storage.py: mime_to_lucide_icon() / SearchHit-Default",
    "row.icon_name": "aus drive_storage.py: mime_to_lucide_icon() / FileRow-Default",
}

_SYMBOL_BLOCK = re.compile(r'<symbol id="([^"]+)">(.*?)</symbol>', re.DOTALL)
_LICENSE = re.compile(r"<!--.*?-->", re.DOTALL)
_JINJA_EXPR = re.compile(r"^\{\{\s*(.+?)\s*\}\}$")
_JINJA_SET_LITERAL = re.compile(
    r"""\{%-?\s*set\s+([A-Za-z_]\w*)\s*=\s*(['"])([^'"]*)\2\s*-?%\}"""
)
_USE_HREF = re.compile(r'<use\s+href="([^"]*)#([^"]*)"')
_LITERAL_ARG = re.compile(r"""^(['"])([^'"]*)\1$""")
_ICON_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

HEADER = """<?xml version="1.0" encoding="utf-8"?>
{license}
<!-- GENERIERT - NICHT VON HAND BEARBEITEN.
     Subset von icons/{full} mit den {count} tatsaechlich benutzten Symbolen.
     Neu bauen: python scripts/build_icon_sprite.py -->
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
  <defs>
"""

FOOTER = """  </defs>
</svg>
"""


@dataclass(frozen=True)
class IconRef:
    """Ein Icon-Name samt Fundstelle - die Fundstelle macht Fehler lesbar."""

    name: str
    origin: str


class BuildError(SystemExit):
    def __init__(self, message: str) -> None:
        super().__init__(f"\nFEHLER: {message}\n")


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _origin(path: Path, text: str, index: int) -> str:
    return f"{_rel(path)}:{text.count(chr(10), 0, index) + 1}"


def _split_call_args(text: str, open_paren: int) -> list[str] | None:
    """Zerlegt die Argumentliste ab `open_paren` in Top-Level-Argumente.

    Klammer- und quote-bewusst, damit ein verschachteltes
    `url_for('a', b='c,d')` nicht faelschlich am Komma zerfaellt.
    `None` bei unbalancierten Klammern.
    """
    depth = 0
    quote: str | None = None
    args: list[str] = []
    current: list[str] = []

    for index in range(open_paren, len(text)):
        char = text[index]
        if quote is not None:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in "'\"":
            quote = char
            current.append(char)
        elif char in "([{":
            depth += 1
            if depth > 1:
                current.append(char)
        elif char in ")]}":
            depth -= 1
            if depth == 0:
                args.append("".join(current).strip())
                return args
            current.append(char)
        elif char == "," and depth == 1:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    return None


def _jinja_set_literals(text: str) -> dict[str, list[str]]:
    """Alle `{% set name = 'literal' %}` eines Templates, Name -> Werte."""
    found: dict[str, list[str]] = {}
    for match in _JINJA_SET_LITERAL.finditer(text):
        found.setdefault(match.group(1), []).append(match.group(3))
    return found


def _resolve_arg(
    arg: str,
    path: Path,
    text: str,
    index: int,
    jinja_literals: dict[str, list[str]],
    what: str,
) -> list[str]:
    """Loest ein Icon-Argument zu Namen auf - oder bricht ab."""
    literal = _LITERAL_ARG.match(arg)
    if literal:
        return [literal.group(2)]

    # Im selben Template gesetzt, etwa flash_icon in _flash_messages.html.
    if arg in jinja_literals:
        return jinja_literals[arg]

    if arg in ALLOWED_DYNAMIC_ARGS:
        return []

    raise BuildError(
        f"{_origin(path, text, index)}: {what} bekommt den Ausdruck "
        f"[{arg}],\n"
        "       den dieses Script nicht aufloesen kann.\n"
        "       Entweder ein String-Literal verwenden, den Wert im selben\n"
        "       Template per set-Tag aus einem Literal setzen, oder den\n"
        "       Ausdruck in ALLOWED_DYNAMIC_ARGS eintragen und eine Quelle\n"
        "       ergaenzen, die die moeglichen Namen liefert."
    )


def _collect_calls(
    path: Path,
    text: str,
    func: str,
    arg_index: int,
    jinja_literals: dict[str, list[str]],
) -> list[IconRef]:
    """Icon-Namen aus dem `arg_index`-ten Argument aller `func(...)`-Aufrufe."""
    refs: list[IconRef] = []
    for match in re.finditer(rf"\b{re.escape(func)}\s*\(", text):
        open_paren = match.end() - 1
        args = _split_call_args(text, open_paren)
        if args is None:
            raise BuildError(
                f"{_origin(path, text, match.start())}: unbalancierte Klammern "
                f"im Aufruf von {func}()"
            )
        if len(args) <= arg_index:
            raise BuildError(
                f"{_origin(path, text, match.start())}: {func}() hat nur "
                f"{len(args)} Argument(e), erwartet werden mindestens "
                f"{arg_index + 1}"
            )
        what = f"{func}(), Argument {arg_index + 1},"
        for name in _resolve_arg(
            args[arg_index], path, text, match.start(), jinja_literals, what
        ):
            refs.append(IconRef(name, _origin(path, text, match.start())))
    return refs


def _collect_use_hrefs(path: Path, text: str) -> list[IconRef]:
    """Icon-Namen aus literalen `<use href="...#name">`-Attributen."""
    refs: list[IconRef] = []
    for match in _USE_HREF.finditer(text):
        fragment = match.group(2)
        if _ICON_NAME.match(fragment):
            refs.append(IconRef(fragment, _origin(path, text, match.start())))
            continue
        expression = _JINJA_EXPR.match(fragment)
        if expression and expression.group(1) in ALLOWED_DYNAMIC_ARGS:
            continue
        raise BuildError(
            f"{_origin(path, text, match.start())}: use-href zeigt auf das "
            f"Fragment [#{fragment}],\n"
            "       das weder ein Icon-Name noch ein bekannter Platzhalter ist.\n"
            "       Bekannte Platzhalter: "
            + ", ".join(sorted(ALLOWED_DYNAMIC_ARGS))
        )
    return refs


def collect_template_refs() -> list[IconRef]:
    """Quellen 1-4: alles, was in den Templates steht."""
    refs: list[IconRef] = []
    for path in [*sorted(TEMPLATES.rglob("*.html")), *EXTRA_HTML]:
        text = path.read_text(encoding="utf-8")
        literals = _jinja_set_literals(text)
        refs += _collect_calls(path, text, "lucide_icon", 0, literals)
        refs += _collect_calls(path, text, "dashboard_intent_tile", 1, literals)
        refs += _collect_use_hrefs(path, text)
    return refs


def collect_js_refs() -> list[IconRef]:
    """Quelle 5: Icons, die JS zur Laufzeit ins DOM schreibt."""
    refs: list[IconRef] = []
    for path in sorted(JS_DIR.rglob("*.js")):
        if FINGERPRINTED.search(path.name):
            continue
        text = path.read_text(encoding="utf-8")
        refs += _collect_calls(path, text, "lucideInlineIcon", 0, {})
    return refs


def collect_python_refs() -> list[IconRef]:
    """Quelle 6: Namen aus backend/services/drive_storage.py.

    Sie erreichen die Docs-Templates als `hit.icon_name` / `row.icon_name` und
    sind dort nicht mehr als Literal sichtbar.
    """
    source = DRIVE_STORAGE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(DRIVE_STORAGE))
    refs: list[IconRef] = []
    seen_mapper = False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "mime_to_lucide_icon":
            seen_mapper = True
            for statement in ast.walk(node):
                if not isinstance(statement, ast.Return):
                    continue
                value = statement.value
                if not (
                    isinstance(value, ast.Constant) and isinstance(value.value, str)
                ):
                    raise BuildError(
                        f"{_rel(DRIVE_STORAGE)}:{statement.lineno}: "
                        "mime_to_lucide_icon() gibt etwas anderes zurueck als\n"
                        "       ein String-Literal. Dieses Script kann die\n"
                        "       moeglichen Icon-Namen dann nicht mehr ablesen."
                    )
                refs.append(
                    IconRef(
                        value.value,
                        f"{_rel(DRIVE_STORAGE)}:{statement.lineno}"
                        " (mime_to_lucide_icon)",
                    )
                )
        elif isinstance(node, ast.ClassDef):
            for statement in node.body:
                if not isinstance(statement, ast.AnnAssign):
                    continue
                target = statement.target
                if not (isinstance(target, ast.Name) and target.id == "icon_name"):
                    continue
                value = statement.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    refs.append(
                        IconRef(
                            value.value,
                            f"{_rel(DRIVE_STORAGE)}:{statement.lineno}"
                            f" ({node.name}-Default)",
                        )
                    )

    if not seen_mapper:
        raise BuildError(
            f"mime_to_lucide_icon() in {_rel(DRIVE_STORAGE)} nicht gefunden - "
            "umbenannt oder verschoben?"
        )
    return refs


def collect_icon_refs() -> list[IconRef]:
    """Alle referenzierten Icons aus allen Quellen."""
    return collect_template_refs() + collect_js_refs() + collect_python_refs()


def parse_symbols(svg_text: str) -> dict[str, str]:
    """Symbol-Name -> roher Inhalt des `<symbol>`-Blocks."""
    symbols = dict(_SYMBOL_BLOCK.findall(svg_text))
    if not symbols:
        raise BuildError("Keine symbol-Elemente im SVG gefunden")
    return symbols


def _license_comment() -> str:
    """Der lucide-static-Lizenzhinweis - ISC verlangt, dass er mitgeht."""
    match = _LICENSE.search(FULL_SPRITE.read_text(encoding="utf-8"))
    if not match:
        raise BuildError(
            f"Kein Lizenz-Kommentar in {_rel(FULL_SPRITE)} gefunden - die "
            "ISC-Lizenz verlangt, dass er im Subset erhalten bleibt."
        )
    return match.group(0)


def build_subset(names: set[str], symbols: dict[str, str]) -> str:
    """Setzt das Subset-SVG zusammen. Sortiert, damit der Hash stabil bleibt."""
    parts = [
        HEADER.format(
            license=_license_comment(), full=FULL_SPRITE.name, count=len(names)
        )
    ]
    for name in sorted(names):
        parts.append(f'    <symbol id="{name}">{symbols[name]}</symbol>\n')
    parts.append(FOOTER)
    return "".join(parts)


def _report_missing(missing: dict[str, list[str]]) -> None:
    lines = [
        f"{len(missing)} referenzierte(s) Symbol(e) gibt es im vollen Sprite nicht:"
    ]
    for name in sorted(missing):
        lines.append(f"  #{name}")
        for origin in sorted(set(missing[name])):
            lines.append(f"      {origin}")
    lines.append("")
    lines.append("       Tippfehler? Die gueltigen Namen: https://lucide.dev/icons/")
    raise BuildError("\n".join(lines))


def main() -> None:
    if not FULL_SPRITE.exists():
        raise BuildError(
            f"{_rel(FULL_SPRITE)} fehlt. Das ist das vollstaendige "
            "lucide-static-Sprite und die Quelle dieses Builds."
        )

    symbols = parse_symbols(FULL_SPRITE.read_text(encoding="utf-8"))
    refs = collect_icon_refs()

    missing: dict[str, list[str]] = {}
    for ref in refs:
        if ref.name not in symbols:
            missing.setdefault(ref.name, []).append(ref.origin)
    if missing:
        _report_missing(missing)

    names = {ref.name for ref in refs}
    SUBSET_SPRITE.write_text(
        build_subset(names, symbols), encoding="utf-8", newline="\n"
    )

    digest = hashlib.sha256(SUBSET_SPRITE.read_bytes()).hexdigest()[:HASH_LEN]
    hashed = SUBSET_SPRITE.with_name(
        f"{SUBSET_SPRITE.stem}.{digest}{SUBSET_SPRITE.suffix}"
    )
    hashed.write_bytes(SUBSET_SPRITE.read_bytes())

    manifest = (
        json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    )
    manifest[_rel(SUBSET_SPRITE)] = _rel(hashed)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    full_kb = FULL_SPRITE.stat().st_size / 1024
    subset_kb = SUBSET_SPRITE.stat().st_size / 1024
    print(
        f"[ok] {len(names)} von {len(symbols)} Symbolen uebernommen "
        f"({subset_kb:.1f} KB statt {full_kb:.1f} KB)"
    )
    print(f"[ok] Fingerprint: {hashed.name}")
    print("\nIn templates/, static/offline.html, static/js/app.js und")
    print("static/sw.js (STATIC_ASSETS) referenzieren als:")
    print(f"  static/icons/{hashed.name}")
    print("\nDanach: python scripts/update_pwa_version.py <version>")


if __name__ == "__main__":
    main()
