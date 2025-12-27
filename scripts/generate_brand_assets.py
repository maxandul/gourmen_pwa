"""
Generate logo assets (favicons, PWA icons, OG images, iOS splash) from master SVGs.

Sources (expected):
- static/brand/logo-master-square.svg (preferred for most assets)
- static/brand/logo-master-round.svg (optional; not required for generation)

Outputs:
- static/favicon.ico / static/favicon.svg
- static/img/pwa/*.png (icons, apple-touch, maskable, splash)
- static/img/og-image-1200x630.png, static/img/og-image-1200.png
"""

from __future__ import annotations

import io
import subprocess
from pathlib import Path
from typing import Iterable, Tuple

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BRAND_DIR = ROOT / "static" / "brand"
OUT_PWA = ROOT / "static" / "img" / "pwa"
OUT_SPLASH = OUT_PWA / "splash"
OUT_IMG = ROOT / "static" / "img"
FAVICON_PATH = ROOT / "static" / "favicon.ico"
FAVICON_SVG_PATH = ROOT / "static" / "favicon.svg"

SQUARE_SVG = BRAND_DIR / "logo-master-square.svg"
ROUND_SVG = BRAND_DIR / "logo-master-round.svg"

BASE_COLOR = "#1b232e"
MASKABLE_SCALE = 0.66  # Foreground scale to keep safe area ~66%
INKSCAPE_BIN = "inkscape"


def svg_to_image(svg_path: Path, size: int) -> Image.Image:
    """
    Render SVG to RGBA PIL image using Inkscape CLI (avoids cairo dependency).
    """
    with io.BytesIO() as buf:
        with Path(svg_path) as src:
            tmp_png = src.with_suffix(f".tmp-{size}.png")
            try:
                cmd = [
                    INKSCAPE_BIN,
                    "--export-type=png",
                    f"--export-filename={tmp_png}",
                    f"--export-width={size}",
                    f"--export-height={size}",
                    str(src),
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                img = Image.open(tmp_png).convert("RGBA")
            finally:
                if tmp_png.exists():
                    try:
                        tmp_png.unlink()
                    except OSError:
                        pass
    return img


def ensure_dirs() -> None:
    OUT_PWA.mkdir(parents=True, exist_ok=True)
    OUT_SPLASH.mkdir(parents=True, exist_ok=True)
    OUT_IMG.mkdir(parents=True, exist_ok=True)


def paste_center(background: Image.Image, foreground: Image.Image) -> Image.Image:
    bg = background.copy()
    x = (bg.width - foreground.width) // 2
    y = (bg.height - foreground.height) // 2
    bg.alpha_composite(foreground, (x, y))
    return bg


def save_png(img: Image.Image, path: Path, remove_alpha: bool = False) -> None:
    if remove_alpha:
        img = img.convert("RGB")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")


def generate_icons(square_svg: Path) -> None:
    print("Generating standard icons...")
    for size, name in [(16, "icon-16.png"), (32, "icon-32.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
        img = svg_to_image(square_svg, size)
        save_png(img, OUT_PWA / name)

    # ICO with multiple sizes for broad compatibility
    ico_base = svg_to_image(square_svg, 256)
    ico_sizes = [16, 32, 48]
    ico_images = [ico_base.resize((s, s), Image.LANCZOS) for s in ico_sizes]
    FAVICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    ico_images[0].save(FAVICON_PATH, format="ICO", sizes=[(s, s) for s in ico_sizes])

    # SVG favicon copy
    FAVICON_SVG_PATH.write_bytes(square_svg.read_bytes())


def generate_maskable(square_svg: Path) -> None:
    print("Generating maskable icons...")
    for size in (192, 512):
        fg = svg_to_image(square_svg, int(size * MASKABLE_SCALE))
        bg = Image.new("RGBA", (size, size), BASE_COLOR)
        composed = paste_center(bg, fg)
        save_png(composed, OUT_PWA / f"icon-{size}-maskable.png")


def generate_apple_touch(square_svg: Path) -> None:
    print("Generating apple-touch icons...")
    for size in (120, 152, 167, 180):
        fg = svg_to_image(square_svg, size)
        # Apple touch prefers no transparency; place on brand background
        bg = Image.new("RGBA", (size, size), BASE_COLOR)
        composed = paste_center(bg, fg)
        save_png(composed, OUT_PWA / f"apple-touch-icon-{size}.png", remove_alpha=True)

    # Keep legacy fallback name
    (OUT_PWA / "apple-touch-icon.png").write_bytes((OUT_PWA / "apple-touch-icon-180.png").read_bytes())


def generate_og(square_svg: Path) -> None:
    print("Generating OG/Twitter images...")
    og_defs = [
        ((1200, 630), OUT_IMG / "og-image-1200x630.png"),
        ((1200, 1200), OUT_IMG / "og-image-1200.png"),
    ]
    for (w, h), path in og_defs:
        bg = Image.new("RGBA", (w, h), BASE_COLOR)
        logo_size = int(min(w, h) * 0.4)
        fg = svg_to_image(square_svg, logo_size)
        composed = paste_center(bg, fg)
        save_png(composed, path, remove_alpha=True)


def generate_splash(square_svg: Path) -> None:
    print("Generating iOS splash screens...")
    # device_width/height are CSS pixel values used in media queries
    specs = [
        ("iphone-se", 320, 568, 2, 640, 1136),
        ("iphone-8", 375, 667, 2, 750, 1334),
        ("iphone-8-plus", 414, 736, 3, 1242, 2208),
        ("iphone-x", 375, 812, 3, 1125, 2436),
        ("iphone-xr", 414, 896, 2, 828, 1792),
        ("iphone-12-mini", 360, 780, 3, 1080, 2340),
        ("iphone-12", 390, 844, 3, 1170, 2532),
        ("iphone-12-pro-max", 428, 926, 3, 1284, 2778),
        ("iphone-14-plus", 430, 932, 3, 1290, 2796),
        ("iphone-15-pro", 393, 852, 3, 1179, 2556),
        # iPad family (portrait)
        ("ipad-mini", 768, 1024, 2, 1536, 2048),
        ("ipad-10th", 810, 1080, 2, 1620, 2160),
        ("ipad-air", 820, 1180, 2, 1640, 2360),
        ("ipad-pro-11", 834, 1194, 2, 1668, 2388),
        ("ipad-pro-12-9", 1024, 1366, 2, 2048, 2732),
    ]

    for name, dev_w, dev_h, ratio, px_w, px_h in specs:
        bg = Image.new("RGBA", (px_w, px_h), BASE_COLOR)
        logo_size = int(min(px_w, px_h) * 0.35)
        fg = svg_to_image(square_svg, logo_size)
        composed = paste_center(bg, fg)
        file_path = OUT_SPLASH / f"splash-{px_w}x{px_h}.png"
        save_png(composed, file_path, remove_alpha=True)

    # Write media query map for reference
    media_map_lines = []
    for name, dev_w, dev_h, ratio, px_w, px_h in specs:
        media = (
            f"(device-width: {dev_w}px) and (device-height: {dev_h}px) and "
            f"(-webkit-device-pixel-ratio: {ratio})"
        )
        media_map_lines.append(f"{name}: {media} -> splash-{px_w}x{px_h}.png")
    (OUT_SPLASH / "splash-media-map.txt").write_text("\n".join(media_map_lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    if not SQUARE_SVG.exists():
        raise FileNotFoundError(f"Master SVG fehlt: {SQUARE_SVG}")

    square_svg = SQUARE_SVG
    generate_icons(square_svg)
    generate_maskable(square_svg)
    generate_apple_touch(square_svg)
    generate_og(square_svg)
    generate_splash(square_svg)
    print("Done.")


if __name__ == "__main__":
    main()

