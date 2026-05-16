#!/usr/bin/env python3
"""
PWA Version Update Script
Aktualisiert automatisch alle Versionsnummern in der Gourmen PWA

Usage:
    python scripts/update_pwa_version.py 1.3.6
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def update_version(new_version: str) -> None:
    """Aktualisiert die PWA-Version in allen relevanten Dateien"""

    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"[FEHLER] Ungueltige Versionsnummer: {new_version}")
        print("          Format: MAJOR.MINOR.PATCH (z. B. 1.3.6)")
        sys.exit(1)

    print(f"Aktualisiere PWA-Version auf {new_version}...")
    print()

    sw_file = Path('static/sw.js')
    if sw_file.exists():
        content = sw_file.read_text(encoding='utf-8')
        new_content, n = re.subn(
            r"const VERSION = '[\d.]+';",
            f"const VERSION = '{new_version}';",
            content,
            count=1,
        )
        if n == 0:
            print("[WARNUNG] static/sw.js: VERSION-Konstante nicht gefunden")
        else:
            sw_file.write_text(new_content, encoding='utf-8')
            print("[OK] static/sw.js aktualisiert")
    else:
        print("[WARNUNG] static/sw.js nicht gefunden")

    base_file = Path('templates/base.html')
    if base_file.exists():
        content = base_file.read_text(encoding='utf-8')
        content = re.sub(
            r'\?v=[\d.]+',
            f'?v={new_version}',
            content,
        )
        base_file.write_text(content, encoding='utf-8')
        print("[OK] templates/base.html aktualisiert")
    else:
        print("[WARNUNG] templates/base.html nicht gefunden")

    pwa_file = Path('static/js/pwa.js')
    if pwa_file.exists():
        content = pwa_file.read_text(encoding='utf-8')
        new_content, n = re.subn(
            r"const PWA_VERSION = '[\d.]+';",
            f"const PWA_VERSION = '{new_version}';",
            content,
            count=1,
        )
        if n == 0:
            print("[WARNUNG] static/js/pwa.js: PWA_VERSION-Konstante nicht gefunden")
        else:
            pwa_file.write_text(new_content, encoding='utf-8')
            print("[OK] static/js/pwa.js aktualisiert")
    else:
        print("[WARNUNG] static/js/pwa.js nicht gefunden")

    print()
    print(f"Fertig: Version auf {new_version} gesetzt.")
    print()
    print("Naechste Schritte:")
    print("   1. Asset-Hashes:  python scripts/fingerprint_assets.py")
    print("      -> Bei geaenderter pwa.js ggf. partials/_head_deferred_scripts.html anpassen.")
    print("   2. Lokal testen:  python start.py")
    print("   3. Commit + Tag:  git commit -am 'Bump PWA to v{0}' && git tag v{0}".format(new_version))
    print("   4. Deploy via Merge auf master.")
    print()


def show_current_versions() -> None:
    """Zeigt die aktuellen Versionen in allen relevanten Dateien"""

    print("Aktuelle Versionen:")
    print()

    sw_file = Path('static/sw.js')
    if sw_file.exists():
        content = sw_file.read_text(encoding='utf-8')
        match = re.search(r"const VERSION = '([\d.]+)';", content)
        if match:
            print(f"   sw.js:        v{match.group(1)}")

    base_file = Path('templates/base.html')
    if base_file.exists():
        content = base_file.read_text(encoding='utf-8')
        match = re.search(r'\?v=([\d.]+)', content)
        if match:
            print(f"   base.html:    v{match.group(1)}")

    pwa_file = Path('static/js/pwa.js')
    if pwa_file.exists():
        content = pwa_file.read_text(encoding='utf-8')
        match = re.search(r"const PWA_VERSION = '([\d.]+)';", content)
        if match:
            print(f"   pwa.js:       v{match.group(1)}")

    print()


def main() -> None:
    if not Path('static/sw.js').exists() and not Path('templates/base.html').exists():
        print("[FEHLER] Script im Projekt-Root ausfuehren!")
        print("         Aktuelles Verzeichnis:", Path.cwd())
        sys.exit(1)

    if len(sys.argv) < 2:
        show_current_versions()
        print("Usage: python scripts/update_pwa_version.py <VERSION>")
        print("       Beispiel: python scripts/update_pwa_version.py 1.3.6")
        sys.exit(0)

    new_version = sys.argv[1].strip()
    if new_version.startswith('v'):
        new_version = new_version[1:]

    update_version(new_version)


if __name__ == '__main__':
    main()
