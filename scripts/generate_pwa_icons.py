import os
from pathlib import Path
from PIL import Image


# Quelle ist das hochauflösende PWA-Icon (512px) aus dem Master-Export
SOURCE = Path('static/img/pwa/icon-512.png')
OUT_DIR = Path('static/img/pwa')

# Zielgrößen
ANY_SIZES = [16, 32, 96, 192, 512]
MASKABLE_SIZES = [192, 512]
APPLE_TOUCH_SIZE = 180  # 180x180

# Hintergrundfarbe für Apple Touch Icon (keine Transparenz erlaubt)
APPLE_BG = (27, 35, 46, 255)  # #1b232e


def ensure_out_dir():
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_source() -> Image.Image:
    if not SOURCE.exists():
        raise FileNotFoundError(f'Quelle nicht gefunden: {SOURCE}')
    img = Image.open(SOURCE).convert('RGBA')
    return img


def resize_cover(img: Image.Image, size: int) -> Image.Image:
    """Skaliert so, dass die Kachel vollständig gefüllt ist (Cover), dann mittig zuschneiden."""
    w, h = img.size
    scale = max(size / w, size / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - size) // 2
    top = (new_h - size) // 2
    right = left + size
    bottom = top + size
    cropped = resized.crop((left, top, right, bottom))
    return cropped


def save_png(img: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format='PNG')


def generate_any_icons(src: Image.Image):
    for s in ANY_SIZES:
        out = resize_cover(src, s)
        save_png(out, OUT_DIR / f'icon-{s}.png')


def generate_maskable_icons(src: Image.Image):
    for s in MASKABLE_SIZES:
        # Für maskable unbedingt vollflächig (cover), ohne Rand/Transparenzräume
        out = resize_cover(src, s)
        save_png(out, OUT_DIR / f'icon-{s}-maskable.png')


def generate_apple_touch_icon(src: Image.Image):
    s = APPLE_TOUCH_SIZE
    cover = resize_cover(src, s)
    # Auf nicht-transparente Fläche legen (iOS mag keine Transparenz für Touch Icons)
    bg = Image.new('RGBA', (s, s), APPLE_BG)
    bg.alpha_composite(cover)
    # Als PNG ohne Alpha speichern (konvertieren zu RGB)
    rgb = bg.convert('RGB')
    save_png(rgb, OUT_DIR / 'apple-touch-icon.png')


def main():
    ensure_out_dir()
    src = load_source()

    generate_any_icons(src)
    generate_maskable_icons(src)
    generate_apple_touch_icon(src)

    print('PWA Icons erfolgreich generiert und in static/img/pwa/ gespeichert.')


if __name__ == '__main__':
    main()


