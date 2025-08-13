#!/usr/bin/env python3
"""
Skript zum Generieren aller benötigten PWA-Icons aus dem Hauptlogo
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import math

def create_icon_sizes():
    """Erstellt alle benötigten Icon-Größen für die PWA"""
    
    # Pfade
    logo_path = "static/img/logo.png"
    output_dir = "static/img"
    
    # Erstelle Output-Verzeichnis falls nicht vorhanden
    os.makedirs(output_dir, exist_ok=True)
    
    # Benötigte Icon-Größen
    sizes = [16, 32, 96, 192, 512]
    
    try:
        # Lade das Original-Logo
        with Image.open(logo_path) as original:
            print(f"Original-Logo geladen: {original.size}")
            
            for size in sizes:
                # Erstelle Icon mit der gewünschten Größe
                icon = original.resize((size, size), Image.Resampling.LANCZOS)
                
                # Füge Padding hinzu für bessere Darstellung
                padded_size = int(size * 1.1)  # 10% Padding
                padded_icon = Image.new('RGBA', (padded_size, padded_size), (0, 0, 0, 0))
                
                # Zentriere das Icon
                offset = (padded_size - size) // 2
                padded_icon.paste(icon, (offset, offset))
                
                # Speichere das Icon
                output_path = os.path.join(output_dir, f"icon-{size}.png")
                padded_icon.save(output_path, "PNG", optimize=True)
                print(f"Icon {size}x{size} erstellt: {output_path}")
                
    except FileNotFoundError:
        print(f"Fehler: Logo nicht gefunden unter {logo_path}")
        return False
    except Exception as e:
        print(f"Fehler beim Erstellen der Icons: {e}")
        return False
    
    return True

def create_apple_touch_icon():
    """Erstellt Apple Touch Icon (180x180)"""
    
    logo_path = "static/img/logo.png"
    output_path = "static/img/apple-touch-icon.png"
    
    try:
        with Image.open(logo_path) as original:
            # Apple Touch Icon sollte 180x180 sein
            icon = original.resize((180, 180), Image.Resampling.LANCZOS)
            icon.save(output_path, "PNG", optimize=True)
            print(f"Apple Touch Icon erstellt: {output_path}")
            return True
    except Exception as e:
        print(f"Fehler beim Erstellen des Apple Touch Icons: {e}")
        return False

def create_favicon():
    """Erstellt Favicon.ico (16x16, 32x32)"""
    
    logo_path = "static/img/logo.png"
    output_path = "static/favicon.ico"
    
    try:
        with Image.open(logo_path) as original:
            # Erstelle 16x16 und 32x32 Icons für favicon.ico
            icons = []
            for size in [16, 32]:
                icon = original.resize((size, size), Image.Resampling.LANCZOS)
                icons.append(icon)
            
            # Speichere als ICO-Datei
            icons[0].save(output_path, format='ICO', sizes=[(16, 16), (32, 32)])
            print(f"Favicon erstellt: {output_path}")
            return True
    except Exception as e:
        print(f"Fehler beim Erstellen des Favicons: {e}")
        return False

def create_maskable_icons():
    """Erstellt maskable Icons mit sicherem Bereich"""
    
    logo_path = "static/img/logo.png"
    output_dir = "static/img"
    
    try:
        with Image.open(logo_path) as original:
            for size in [192, 512]:
                # Erstelle größeres Canvas für maskable Icon
                canvas_size = int(size * 1.2)  # 20% größer für sicheren Bereich
                canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
                
                # Resize Logo
                icon = original.resize((size, size), Image.Resampling.LANCZOS)
                
                # Zentriere das Icon
                offset = (canvas_size - size) // 2
                canvas.paste(icon, (offset, offset))
                
                # Speichere als maskable Icon
                output_path = os.path.join(output_dir, f"icon-{size}-maskable.png")
                canvas.save(output_path, "PNG", optimize=True)
                print(f"Maskable Icon {size}x{size} erstellt: {output_path}")
                
    except Exception as e:
        print(f"Fehler beim Erstellen der maskable Icons: {e}")
        return False
    
    return True

def main():
    """Hauptfunktion"""
    print("🚀 PWA Icon Generator für Gourmen")
    print("=" * 40)
    
    success = True
    
    # Erstelle alle Icon-Größen
    if create_icon_sizes():
        print("✅ Alle Icon-Größen erstellt")
    else:
        success = False
    
    # Erstelle Apple Touch Icon
    if create_apple_touch_icon():
        print("✅ Apple Touch Icon erstellt")
    else:
        success = False
    
    # Erstelle Favicon
    if create_favicon():
        print("✅ Favicon erstellt")
    else:
        success = False
    
    # Erstelle maskable Icons
    if create_maskable_icons():
        print("✅ Maskable Icons erstellt")
    else:
        success = False
    
    print("=" * 40)
    if success:
        print("🎉 Alle Icons erfolgreich erstellt!")
        print("\nNächste Schritte:")
        print("1. Überprüfe die erstellten Icons in static/img/")
        print("2. Teste die PWA-Installation")
        print("3. Überprüfe das neue Design")
    else:
        print("❌ Einige Icons konnten nicht erstellt werden")
        sys.exit(1)

if __name__ == "__main__":
    main()



