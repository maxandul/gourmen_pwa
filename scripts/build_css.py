"""Baut das V2-CSS-Bundle aus den Quelldateien unter static/css/v2/.

Hintergrund: main-v2.css bestand frueher nur aus @import-Zeilen. Der Browser
musste damit erst main-v2.css laden und parsen, bevor er die vier eigentlichen
Stylesheets anfordern konnte - ein render-blockierender Wasserfall, der in
langsamen Netzen (Firmenproxy) reisst und die Seite unformatiert zurueck laesst.

Dieses Script konkateniert die Quellen in Kaskaden-Reihenfolge zu einer Datei,
fingerprintet sie und traegt sie ins Asset-Manifest ein. Ergebnis: ein Request
statt fuenf.

Aufruf:  python scripts/build_css.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CSS = STATIC / "css"
MANIFEST = STATIC / "asset-manifest.json"

# Kaskaden-Reihenfolge - entspricht der frueheren @import-Reihenfolge in main-v2.css.
SOURCES = [
    "v2/tokens.css",      # Design Tokens & Theme Variables
    "v2/base.css",        # Reset, Typography, Base Elements
    "v2/layout.css",      # Base Layout
    "v2/components.css",  # Komponenten
]

BUNDLE = "main-v2.css"
HASH_LEN = 8

HEADER = """/* ================================================================
   GOURMEN PWA - MAIN STYLESHEET V2 (GENERIERT)
   ================================================================
   NICHT VON HAND BEARBEITEN.
   Quellen: {sources}
   Neu bauen: python scripts/build_css.py
   ================================================================ */
"""


def build() -> str:
    parts = [HEADER.format(sources=", ".join("css/" + s for s in SOURCES))]
    for rel in SOURCES:
        src = CSS / rel
        if not src.exists():
            raise SystemExit(f"Quelldatei fehlt: {src}")
        parts.append(f"\n/* ---- {rel} ---- */\n")
        parts.append(src.read_text(encoding="utf-8"))
    return "".join(parts)


def main() -> None:
    content = build()
    bundle_path = CSS / BUNDLE
    bundle_path.write_text(content, encoding="utf-8", newline="\n")

    digest = hashlib.sha256(bundle_path.read_bytes()).hexdigest()[:HASH_LEN]
    hashed = bundle_path.with_name(f"{bundle_path.stem}.{digest}{bundle_path.suffix}")
    hashed.write_bytes(bundle_path.read_bytes())

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    manifest["static/css/main-v2.css"] = f"static/css/{hashed.name}"
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    size_kb = bundle_path.stat().st_size / 1024
    print(f"[ok] {BUNDLE} gebaut aus {len(SOURCES)} Quellen ({size_kb:.1f} KB)")
    print(f"[ok] Fingerprint: {hashed.name}")
    print("\nIn Templates/sw.js referenzieren als:")
    print(f"  static/css/{hashed.name}")


if __name__ == "__main__":
    main()
