#!/usr/bin/env python
"""
Generate PWA Icons from source image
Erstellt alle benötigten Icons für Android und iOS aus einem Source-Icon
"""

from PIL import Image
import os

# Pfade
SOURCE_ICON = 'static/img/pwa/app-icon.png'
OUTPUT_DIR = 'static/img/pwa'

# Icon-Konfigurationen
ICONS = {
    # Android Icons (normale)
    'icon-16.png': 16,
    'icon-32.png': 32,
    'icon-96.png': 96,
    'icon-192.png': 192,
    'icon-512.png': 512,
    
    # iOS Icon
    'apple-touch-icon.png': 180,
    
    # Badge Icons (monochrom für Notifications)
    'badge-72.png': 72,
    'badge-96.png': 96,
}

# Maskable Icons (mit extra Safe Zone - 20% Padding)
MASKABLE_ICONS = {
    'icon-192-maskable.png': 192,
    'icon-512-maskable.png': 512,
}

def create_icon(source_path, output_path, size, maskable=False):
    """
    Erstellt ein Icon in der angegebenen Größe
    
    Args:
        source_path: Pfad zum Source-Icon
        output_path: Pfad für das Output-Icon
        size: Zielgröße (Quadrat)
        maskable: Wenn True, wird Safe Zone Padding hinzugefügt
    """
    try:
        # Öffne Source-Image
        img = Image.open(source_path)
        
        # Konvertiere zu RGBA wenn nötig
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        if maskable:
            # Für maskable Icons: Bild auf 80% verkleinern und zentrieren
            # Android schneidet bis zu 20% des Icons ab für verschiedene Formen
            safe_zone_size = int(size * 0.8)
            
            # Erstelle neues transparentes Bild in voller Größe
            canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            
            # Resize das Originalbild auf Safe Zone Größe
            img_resized = img.resize((safe_zone_size, safe_zone_size), Image.Resampling.LANCZOS)
            
            # Zentriere das verkleinerte Bild auf dem Canvas
            offset = (size - safe_zone_size) // 2
            canvas.paste(img_resized, (offset, offset), img_resized)
            
            img = canvas
        else:
            # Normale Icons: Direkt auf Zielgröße skalieren
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Speichere das Icon
        img.save(output_path, 'PNG', optimize=True)
        print(f"✅ Created: {output_path} ({size}x{size}{'px - maskable' if maskable else 'px'})")
        
    except Exception as e:
        print(f"❌ Error creating {output_path}: {e}")

def main():
    """Hauptfunktion zum Generieren aller Icons"""
    
    # Prüfe ob Source-Icon existiert
    if not os.path.exists(SOURCE_ICON):
        print(f"❌ Source icon not found: {SOURCE_ICON}")
        print(f"   Please make sure 'app-icon.png' exists in {OUTPUT_DIR}")
        return
    
    print(f"🎨 Generating PWA icons from: {SOURCE_ICON}")
    print(f"📁 Output directory: {OUTPUT_DIR}\n")
    
    # Erstelle Output-Verzeichnis falls nötig
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Erstelle normale Icons
    print("📱 Creating standard icons...")
    for filename, size in ICONS.items():
        output_path = os.path.join(OUTPUT_DIR, filename)
        create_icon(SOURCE_ICON, output_path, size, maskable=False)
    
    print("\n🎭 Creating maskable icons (with safe zone padding)...")
    # Erstelle maskable Icons
    for filename, size in MASKABLE_ICONS.items():
        output_path = os.path.join(OUTPUT_DIR, filename)
        create_icon(SOURCE_ICON, output_path, size, maskable=True)
    
    print("\n✨ Icon generation complete!")
    print("\n📋 Generated icons:")
    print("   • Android: icon-192.png, icon-512.png")
    print("   • Android (adaptive): icon-192-maskable.png, icon-512-maskable.png")
    print("   • iOS: apple-touch-icon.png")
    print("   • Various sizes: 16, 32, 96 px")
    print("   • Badges: 72, 96 px")

if __name__ == '__main__':
    main()

