#!/usr/bin/env python3
"""
Skript zum Generieren von Splash Screens für verschiedene iOS-Geräte
"""

import os
from PIL import Image, ImageDraw, ImageFont
import math

def create_splash_screen(width, height, filename):
    """Erstellt einen Splash Screen mit dem Gourmen Logo"""
    
    # Erstelle ein neues Bild mit den gewünschten Dimensionen
    image = Image.new('RGB', (width, height), '#1b232e')
    draw = ImageDraw.Draw(image)
    
    # Lade das Logo
    try:
        logo = Image.open('static/img/logo.png')
        
        # Berechne die Größe für das Logo (20% der Bildschirmbreite)
        logo_size = int(width * 0.2)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Zentriere das Logo
        logo_x = (width - logo_size) // 2
        logo_y = (height - logo_size) // 2 - 50  # Etwas nach oben verschieben
        
        # Füge das Logo hinzu
        image.paste(logo, (logo_x, logo_y), logo if logo.mode == 'RGBA' else None)
        
        # Füge Text hinzu
        try:
            # Versuche eine moderne Schriftart zu verwenden
            font_size = int(width * 0.04)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Fallback auf Standard-Schriftart
            font = ImageFont.load_default()
        
        # App-Name
        app_name = "Gourmen"
        text_bbox = draw.textbbox((0, 0), app_name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2
        text_y = logo_y + logo_size + 30
        
        # Zeichne Text mit Schatten
        shadow_offset = 2
        draw.text((text_x + shadow_offset, text_y + shadow_offset), app_name, fill='#354e5e', font=font)
        draw.text((text_x, text_y), app_name, fill='#ffffff', font=font)
        
        # Untertitel
        subtitle = "Verein Webapp"
        subtitle_font_size = int(font_size * 0.6)
        try:
            subtitle_font = ImageFont.truetype("arial.ttf", subtitle_font_size)
        except:
            subtitle_font = ImageFont.load_default()
        
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (width - subtitle_width) // 2
        subtitle_y = text_y + font_size + 10
        
        draw.text((subtitle_x + shadow_offset, subtitle_y + shadow_offset), subtitle, fill='#354e5e', font=subtitle_font)
        draw.text((subtitle_x, subtitle_y), subtitle, fill='#dc693c', font=subtitle_font)
        
    except FileNotFoundError:
        # Fallback wenn kein Logo gefunden wird
        draw.text((width//2, height//2), "Gourmen", fill='#ffffff', anchor="mm")
    
    # Speichere das Bild
    output_path = f'static/img/{filename}'
    image.save(output_path, 'PNG', optimize=True)
    print(f"Splash Screen erstellt: {output_path} ({width}x{height})")

def main():
    """Hauptfunktion"""
    print("🎨 Splash Screen Generator für Gourmen")
    print("=" * 40)
    
    # Erstelle Output-Verzeichnis
    os.makedirs('static/img', exist_ok=True)
    
    # iOS Splash Screen Größen
    splash_screens = [
        # iPhone 14 Pro Max
        (430, 932, 'splash-430x932.png'),
        # iPhone 14 Pro
        (393, 852, 'splash-393x852.png'),
        # iPhone 14 Plus
        (428, 926, 'splash-428x926.png'),
        # iPhone 14
        (390, 844, 'splash-390x844.png'),
        # iPhone 13 Pro Max
        (428, 926, 'splash-428x926.png'),
        # iPhone 13 Pro
        (390, 844, 'splash-390x844.png'),
        # iPhone 13
        (390, 844, 'splash-390x844.png'),
        # iPhone 12 Pro Max
        (428, 926, 'splash-428x926.png'),
        # iPhone 12 Pro
        (390, 844, 'splash-390x844.png'),
        # iPhone 12
        (390, 844, 'splash-390x844.png'),
        # iPhone 11 Pro Max
        (414, 896, 'splash-414x896.png'),
        # iPhone 11 Pro
        (375, 812, 'splash-375x812.png'),
        # iPhone 11
        (414, 896, 'splash-414x896.png'),
        # iPhone XS Max
        (414, 896, 'splash-414x896.png'),
        # iPhone XS
        (375, 812, 'splash-375x812.png'),
        # iPhone XR
        (414, 896, 'splash-414x896.png'),
        # iPhone X
        (375, 812, 'splash-375x812.png'),
        # iPhone 8 Plus
        (414, 736, 'splash-414x736.png'),
        # iPhone 8
        (375, 667, 'splash-375x667.png'),
        # iPhone SE (2nd gen)
        (375, 667, 'splash-375x667.png'),
        # iPhone SE (1st gen)
        (320, 568, 'splash-320x568.png'),
    ]
    
    # Entferne Duplikate basierend auf Dateinamen
    unique_screens = {}
    for width, height, filename in splash_screens:
        if filename not in unique_screens:
            unique_screens[filename] = (width, height, filename)
    
    # Erstelle Splash Screens
    for width, height, filename in unique_screens.values():
        create_splash_screen(width, height, filename)
    
    print("=" * 40)
    print(f"✅ {len(unique_screens)} Splash Screens erfolgreich erstellt!")
    print("\nNächste Schritte:")
    print("1. Überprüfe die erstellten Splash Screens in static/img/")
    print("2. Teste die PWA-Installation auf verschiedenen iOS-Geräten")
    print("3. Überprüfe das neue Design")

if __name__ == "__main__":
    main()



