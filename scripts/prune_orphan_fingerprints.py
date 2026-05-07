"""Entfernt alte Hash-Kopien aus static/, die nicht der aktuellen asset-manifest-Zuordnung entsprechen.

Nach mehreren `fingerprint_assets.py`-Lauefen sammeln sich alte main-v2.* / components.* / app.* / pwa.* / offline.*-Dateien.
Aufruf: python scripts/prune_orphan_fingerprints.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "static" / "asset-manifest.json"


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    keep_names = set()
    for src, dst in data.items():
        keep_names.add(Path(dst).name)
    static = ROOT / "static"
    removed: list[Path] = []

    for p in (static / "css").glob("main-v2.*.css"):
        if p.name not in keep_names:
            p.unlink(missing_ok=True)
            removed.append(p)
    for p in (static / "css").glob("public.*.css"):
        if p.name not in keep_names:
            p.unlink(missing_ok=True)
            removed.append(p)
    for p in (static / "css" / "v2").glob("components.*.css"):
        if p.name not in keep_names:
            p.unlink(missing_ok=True)
            removed.append(p)
    for p in (static / "js").glob("app.*.js"):
        if p.name not in keep_names:
            p.unlink(missing_ok=True)
            removed.append(p)
    for p in (static / "js").glob("pwa.*.js"):
        if p.name not in keep_names:
            p.unlink(missing_ok=True)
            removed.append(p)
    for p in static.glob("offline.*.html"):
        if p.name not in keep_names:
            p.unlink(missing_ok=True)
            removed.append(p)

    print(f"Behalten laut Manifest: {sorted(keep_names)}")
    print(f"Entfernt: {len(removed)} Dateien")


if __name__ == "__main__":
    main()
