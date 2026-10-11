"""
Fingerprint ausgewählte statische Assets mittels Content-Hash.

Erzeugt Kopien mit Hash im Dateinamen (z.B. icon-192.<hash>.png) und schreibt
ein Manifest unter static/asset-manifest.json mit Mapping:
{
  "static/img/pwa/icon-192.png": "static/img/pwa/icon-192.abcdef12.png",
  ...
}

Hinweise:
- Original-Dateien bleiben unverändert.
- Script überschreibt vorhandene Hash-Kopien bei erneutem Lauf.
- Passe die FILES-Liste an, wenn weitere Assets gehasht werden sollen.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
MANIFEST_OUT = STATIC / "asset-manifest.json"

# Liste der zu hashenden Dateien (relativ zu /static)
#
# NICHT aufnehmen: Assets, die ein eigenes Build-Script erzeugt - css/main-v2.css
# (build_css.py) und icons/lucide-sprite.svg (build_icon_sprite.py). Diese
# Scripts schreiben Artefakt, Hash-Kopie und Manifest-Eintrag in einem Zug.
# Wuerde dieses Script sie noch einmal hashen, kaeme unter Windows ein anderer
# Hash heraus: die Build-Scripts schreiben mit LF (und git speichert LF), im
# Arbeitsverzeichnis liegt die Datei mit core.autocrlf aber als CRLF. Das
# Manifest zeigte dann auf eine Hash-Kopie, die kein Template referenziert.
FILES = [
    "css/public.css",
    "css/v2/components.css",
    "js/app.js",
    "js/pwa.js",
    "favicon.ico",
    "favicon.svg",
    "img/pwa/icon-16.png",
    "img/pwa/icon-32.png",
    "img/pwa/icon-192.png",
    "img/pwa/icon-512.png",
    "img/pwa/icon-192-maskable.png",
    "img/pwa/icon-512-maskable.png",
    "img/pwa/apple-touch-icon-120.png",
    "img/pwa/apple-touch-icon-152.png",
    "img/pwa/apple-touch-icon-167.png",
    "img/pwa/apple-touch-icon-180.png",
    "img/pwa/badge-72.png",
    "img/pwa/badge-96.png",
    "img/og-image-1200x630.png",
    "img/og-image-1200.png",
    "img/pwa/splash/splash-640x1136.png",
    "img/pwa/splash/splash-750x1334.png",
    "img/pwa/splash/splash-1080x2340.png",
    "img/pwa/splash/splash-1125x2436.png",
    "img/pwa/splash/splash-1170x2532.png",
    "img/pwa/splash/splash-1179x2556.png",
    "img/pwa/splash/splash-1242x2208.png",
    "img/pwa/splash/splash-1284x2778.png",
    "img/pwa/splash/splash-1290x2796.png",
    "img/pwa/splash/splash-1536x2048.png",
    "img/pwa/splash/splash-1620x2160.png",
    "img/pwa/splash/splash-1640x2360.png",
    "img/pwa/splash/splash-1668x2388.png",
    "img/pwa/splash/splash-2048x2732.png",
    "offline.html",
]

HASH_LEN = 8


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:HASH_LEN]


def add_hash_to_name(path: Path, hash_part: str) -> Path:
    stem = path.stem
    suffix = path.suffix
    return path.with_name(f"{stem}.{hash_part}{suffix}")


def main() -> None:
    # Bestehendes Manifest einlesen und nur die FILES-Eintraege aktualisieren.
    # Frueher wurde die Datei komplett neu geschrieben - damit verschwanden bei
    # jedem Lauf die Eintraege der anderen Build-Scripts (build_web_logo.py,
    # build_icon_sprite.py), die hier bewusst nicht in FILES stehen. Das ist
    # gefaehrlich, weil prune_orphan_fingerprints.py das Manifest als
    # Keep-Liste liest: ein verlorener Eintrag heisst geloeschte Live-Datei.
    mapping: dict[str, str] = (
        json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        if MANIFEST_OUT.exists()
        else {}
    )

    for rel in FILES:
        src = STATIC / rel
        if not src.exists():
            print(f"⚠️  Übersprungen (nicht gefunden): {rel}")
            continue
        digest = hash_file(src)
        dst = add_hash_to_name(src, digest)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        mapping[str(src.relative_to(ROOT)).replace("\\", "/")] = str(dst.relative_to(ROOT)).replace("\\", "/")
        print(f"[ok] {rel} -> {dst.name}")

    # Eintraege, deren Ziel es nicht mehr gibt, sind Karteileichen: sie liefern
    # 404 aus, sobald jemand sie referenziert, und verstecken sich sonst still
    # im Manifest. Nur melden, nicht entfernen - fremde Build-Scripts laufen
    # womoeglich erst spaeter.
    verwaist = sorted(dst for dst in mapping.values() if not (ROOT / dst).exists())
    for dst in verwaist:
        print(f"⚠️  Manifest zeigt auf eine fehlende Datei: {dst}")

    MANIFEST_OUT.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"\nManifest geschrieben: {MANIFEST_OUT} ({len(mapping)} Einträge)")


if __name__ == "__main__":
    main()

