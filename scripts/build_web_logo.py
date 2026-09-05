"""Erzeugt web-taugliche Logo-Bitmaps aus dem Master-Asset.

Hintergrund: static/brand/logo-master-round.svg ist kein Vektor-Logo, sondern
ein 1300x1300-PNG plus C2PA-Metadaten, in ein SVG gewickelt - 2.85 MB. Die
Datei wurde auf JEDER Seite geladen (Landing-Hero, User-Bar, Dashboard,
Favicon) und war damit mit Abstand der groesste Posten der Seite. Angezeigt
wird sie nie groesser als 200 CSS-Pixel.

Das SVG macht zwei Dinge, die hier nachgebildet werden muessen:
  1. Es platziert die Bitmap ueber eine `matrix(...)`-Transformation im
     viewBox-Koordinatensystem (skaliert und verschoben).
  2. Es beschneidet das Ganze per clipPath auf einen Kreis - die runde Form
     steckt NICHT in der Bitmap, die ist ein deckendes RGB-Quadrat.

Wer nur die Bitmap extrahiert und skaliert, bekommt ein dunkles Quadrat.

Das Master-SVG bleibt unangetastet - es ist die Quelle fuer
scripts/generate_brand_assets.py.

Aufruf:  python scripts/build_web_logo.py
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
MASTER = STATIC / "brand" / "logo-master-round.svg"
OUT_DIR = STATIC / "img" / "brand"
MANIFEST = STATIC / "asset-manifest.json"

# 256 fuer die kleinen Einsatzorte (User-Bar, Dashboard-Hero), 512 fuer den
# Landing-Hero auf hochaufloesenden Displays (200 CSS-Pixel bei DPR 2).
SIZES = (256, 512)
HASH_LEN = 8

# WebP statt PNG: bei diesem Motiv (fotografisch anmutende Illustration) ist
# PNG um den Faktor 7 groesser, ohne sichtbaren Unterschied. Qualitaet 90 haelt
# die Logo-Kanten sauber.
WEBP_QUALITY = 90

# Kantenglaettung der Kreismaske: Maske in 4-facher Aufloesung zeichnen und
# herunterskalieren.
MASK_SUPERSAMPLE = 4

_EMBEDDED_PNG = re.compile(r"data:image/png;base64,([A-Za-z0-9+/=]+)")
_VIEWBOX = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')
_MATRIX = re.compile(
    r"matrix\(\s*([-\d.]+),\s*[-\d.]+,\s*[-\d.]+,\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\s*\)"
)


def parse_master() -> tuple[Image.Image, float, float, float, float]:
    """Liefert (Bitmap, viewBox-Kantenlaenge, Skalierung, dx, dy) aus dem Master-SVG."""
    svg = MASTER.read_text(encoding="utf-8", errors="ignore")

    png_match = _EMBEDDED_PNG.search(svg)
    if not png_match:
        raise SystemExit(f"Keine eingebettete Bitmap in {MASTER} gefunden")
    bitmap = Image.open(io.BytesIO(base64.b64decode(png_match.group(1)))).convert("RGB")

    vb_match = _VIEWBOX.search(svg)
    if not vb_match:
        raise SystemExit(f"Keine viewBox in {MASTER} gefunden")
    vb_w, vb_h = float(vb_match.group(1)), float(vb_match.group(2))
    if abs(vb_w - vb_h) > 1:
        raise SystemExit(f"viewBox ist nicht quadratisch: {vb_w}x{vb_h}")

    # Die letzte matrix() im Dokument platziert die Bitmap.
    matrices = _MATRIX.findall(svg)
    if not matrices:
        raise SystemExit(f"Keine Platzierungs-Matrix in {MASTER} gefunden")
    sx, sy, dx, dy = (float(v) for v in matrices[-1])
    if abs(sx - sy) > 1e-6:
        raise SystemExit(f"Ungleiche Skalierung in der Matrix: {sx} / {sy}")

    return bitmap, vb_w, sx, dx, dy


def circular_mask(size: int) -> Image.Image:
    """Weiche Kreismaske - der clipPath des Masters ist ein Vollkreis."""
    big = size * MASK_SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def render(bitmap: Image.Image, viewbox: float, scale: float, dx: float, dy: float, size: int) -> Image.Image:
    """Bildet die SVG-Darstellung bei Kantenlaenge `size` nach."""
    unit = size / viewbox  # viewBox-Einheiten -> Zielpixel

    placed_size = max(1, round(bitmap.width * scale * unit))
    placed = bitmap.resize((placed_size, placed_size), Image.LANCZOS)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(placed, (round(dx * unit), round(dy * unit)))
    canvas.putalpha(circular_mask(size))
    return canvas


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bitmap, viewbox, scale, dx, dy = parse_master()
    print(f"Master-Bitmap: {bitmap.size[0]}x{bitmap.size[1]}, viewBox {viewbox:g}, "
          f"scale {scale:g}, offset ({dx:g}, {dy:g})")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    original_kb = MASTER.stat().st_size / 1024

    for size in SIZES:
        img = render(bitmap, viewbox, scale, dx, dy, size)
        path = OUT_DIR / f"logo-round-{size}.webp"
        img.save(path, format="WEBP", quality=WEBP_QUALITY, method=6, lossless=False)

        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:HASH_LEN]
        hashed = path.with_name(f"{path.stem}.{digest}{path.suffix}")
        hashed.write_bytes(path.read_bytes())

        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        manifest[rel] = str(hashed.relative_to(ROOT)).replace("\\", "/")

        print(f"[ok] {hashed.name}  {path.stat().st_size / 1024:.0f} KB  (statt {original_kb:.0f} KB)")

    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest aktualisiert: {MANIFEST}")
    print("Neue Dateinamen in templates/ und static/sw.js nachziehen.")


if __name__ == "__main__":
    main()
