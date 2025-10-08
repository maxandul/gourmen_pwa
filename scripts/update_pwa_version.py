#!/usr/bin/env python3
"""
PWA Version Update Script
Aktualisiert automatisch alle Versionsnummern in der Gourmen PWA

Usage:
    python scripts/update_pwa_version.py 1.3.6
"""

import sys
import re
from pathlib import Path


def update_version(new_version: str) -> None:
    """Aktualisiert die PWA-Version in allen relevanten Dateien"""
    
    # Validiere Versionsnummer
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"❌ Ungültige Versionsnummer: {new_version}")
        print("   Format: MAJOR.MINOR.PATCH (z.B. 1.3.6)")
        sys.exit(1)
    
    print(f"🔄 Aktualisiere PWA-Version auf {new_version}...")
    print()
    
    # 1. Service Worker (sw.js)
    sw_file = Path('static/sw.js')
    if sw_file.exists():
        content = sw_file.read_text(encoding='utf-8')
        
        # Ersetze alle Cache-Namen
        content = re.sub(
            r"const CACHE_NAME = 'gourmen-v[\d.]+';",
            f"const CACHE_NAME = 'gourmen-v{new_version}';",
            content
        )
        content = re.sub(
            r"const STATIC_CACHE = 'gourmen-static-v[\d.]+';",
            f"const STATIC_CACHE = 'gourmen-static-v{new_version}';",
            content
        )
        content = re.sub(
            r"const DYNAMIC_CACHE = 'gourmen-dynamic-v[\d.]+';",
            f"const DYNAMIC_CACHE = 'gourmen-dynamic-v{new_version}';",
            content
        )
        
        sw_file.write_text(content, encoding='utf-8')
        print("✅ static/sw.js aktualisiert")
    else:
        print("⚠️  static/sw.js nicht gefunden")
    
    # 2. Base Template (base.html)
    base_file = Path('templates/base.html')
    if base_file.exists():
        content = base_file.read_text(encoding='utf-8')
        
        # Ersetze Script-Versionen
        content = re.sub(
            r'\?v=[\d.]+',
            f'?v={new_version}',
            content
        )
        
        base_file.write_text(content, encoding='utf-8')
        print("✅ templates/base.html aktualisiert")
    else:
        print("⚠️  templates/base.html nicht gefunden")
    
    # 3. PWA JavaScript (pwa.js)
    pwa_file = Path('static/js/pwa.js')
    if pwa_file.exists():
        content = pwa_file.read_text(encoding='utf-8')
        
        # Ersetze App-Version in updateAppInfo()
        content = re.sub(
            r"versionSpan\.textContent = '[^']+';",
            f"versionSpan.textContent = '{new_version}';",
            content
        )
        
        pwa_file.write_text(content, encoding='utf-8')
        print("✅ static/js/pwa.js aktualisiert")
    else:
        print("⚠️  static/js/pwa.js nicht gefunden")
    
    print()
    print(f"🎉 Version erfolgreich auf {new_version} aktualisiert!")
    print()
    print("📋 Nächste Schritte:")
    print("   1. Änderungen testen: python start.py")
    print("   2. Git Commit: git commit -am 'Bump version to v{}'".format(new_version))
    print("   3. Git Tag: git tag v{}".format(new_version))
    print("   4. Deployment durchführen")
    print()


def show_current_versions() -> None:
    """Zeigt die aktuellen Versionen in allen Dateien"""
    
    print("📊 Aktuelle Versionen:")
    print()
    
    # Service Worker
    sw_file = Path('static/sw.js')
    if sw_file.exists():
        content = sw_file.read_text(encoding='utf-8')
        match = re.search(r"const CACHE_NAME = 'gourmen-v([\d.]+)';", content)
        if match:
            print(f"   sw.js:        v{match.group(1)}")
    
    # Base Template
    base_file = Path('templates/base.html')
    if base_file.exists():
        content = base_file.read_text(encoding='utf-8')
        match = re.search(r'\?v=([\d.]+)', content)
        if match:
            print(f"   base.html:    v{match.group(1)}")
    
    # PWA JavaScript
    pwa_file = Path('static/js/pwa.js')
    if pwa_file.exists():
        content = pwa_file.read_text(encoding='utf-8')
        match = re.search(r"versionSpan\.textContent = '([\d.]+)';", content)
        if match:
            print(f"   pwa.js:       v{match.group(1)}")
    
    print()


def main():
    """Hauptfunktion"""
    
    # Prüfe ob wir im richtigen Verzeichnis sind
    if not Path('static/sw.js').exists() and not Path('templates/base.html').exists():
        print("❌ Fehler: Dieses Script muss aus dem Projekt-Root ausgeführt werden!")
        print("   Aktuelles Verzeichnis:", Path.cwd())
        sys.exit(1)
    
    # Zeige aktuelle Versionen wenn kein Argument
    if len(sys.argv) < 2:
        show_current_versions()
        print("💡 Usage: python scripts/update_pwa_version.py <VERSION>")
        print("   Beispiel: python scripts/update_pwa_version.py 1.3.6")
        sys.exit(0)
    
    # Hole neue Version
    new_version = sys.argv[1].strip()
    
    # Entferne optionales 'v' Präfix
    if new_version.startswith('v'):
        new_version = new_version[1:]
    
    # Aktualisiere Version
    update_version(new_version)


if __name__ == '__main__':
    main()

