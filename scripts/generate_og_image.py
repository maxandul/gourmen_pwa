#!/usr/bin/env python
"""
Generate Open Graph Image (1200x630px) for social media sharing
"""

from PIL import Image, ImageDraw
import os

# Pfade
SOURCE_LOGO = 'static/img/pwa/icon-512.png'
OUTPUT_IMAGE = 'static/img/og-image-1200x630.png'

# Open Graph empfohlene Größe
OG_WIDTH = 1200
OG_HEIGHT = 630

# Hintergrundfarbe (Gourmen Dark Blue)
BACKGROUND_COLOR = '#1b232e'

def create_og_image():
    """Erstellt ein optimiertes Open Graph Bild"""
    
    try:
        # Prüfe ob Logo existiert
        if not os.path.exists(SOURCE_LOGO):
            print(f"❌ Logo not found: {SOURCE_LOGO}")
            return False
        
        print(f"🎨 Creating Open Graph image (1200x630px)...")
        
        # Erstelle Canvas mit Hintergrundfarbe
        canvas = Image.new('RGB', (OG_WIDTH, OG_HEIGHT), BACKGROUND_COLOR)
        
        # Öffne Logo
        logo = Image.open(SOURCE_LOGO)
        
        # Konvertiere zu RGBA wenn nötig
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        # Berechne Größe des Logos (80% der Canvas-Höhe, max 80% der Breite)
        max_height = int(OG_HEIGHT * 0.8)
        max_width = int(OG_WIDTH * 0.8)
        
        # Berechne Skalierung unter Beibehaltung des Seitenverhältnisses
        logo_width, logo_height = logo.size
        scale = min(max_width / logo_width, max_height / logo_height)
        
        new_width = int(logo_width * scale)
        new_height = int(logo_height * scale)
        
        # Resize Logo
        logo_resized = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Zentriere Logo auf Canvas
        x = (OG_WIDTH - new_width) // 2
        y = (OG_HEIGHT - new_height) // 2
        
        # Paste Logo (mit Alpha-Kanal für Transparenz)
        canvas.paste(logo_resized, (x, y), logo_resized)
        
        # Speichere
        canvas.save(OUTPUT_IMAGE, 'PNG', optimize=True, quality=95)
        
        print(f"✅ Open Graph image created: {OUTPUT_IMAGE}")
        print(f"   Size: {OG_WIDTH}x{OG_HEIGHT}px")
        print(f"   Logo size: {new_width}x{new_height}px")
        print(f"   Background: {BACKGROUND_COLOR}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating Open Graph image: {e}")
        return False

if __name__ == '__main__':
    success = create_og_image()
    if success:
        print("\n✨ Open Graph image ready for social media sharing!")
        print("   WhatsApp, Facebook, LinkedIn, Twitter will show this image")
    else:
        print("\n❌ Failed to create Open Graph image")

