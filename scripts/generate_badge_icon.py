#!/usr/bin/env python3
"""
Generiert ein monochromes Badge-Icon für Android Push-Benachrichtigungen
Badge-Icons sollten monochrom (weiß/transparent) sein für die Statusleiste
"""

from PIL import Image, ImageDraw
import os

def create_badge_icon():
    """Erstellt ein einfaches monochromes Badge-Icon"""
    
    # Badge-Icon Größe (typisch 96x96 für Android)
    size = 96
    
    # Erstelle ein transparentes Bild
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Zeichne ein einfaches Icon (z.B. ein "G" für Gourmen)
    # Oder eine stilisierte Gabel/Messer-Silhouette
    
    # Option 1: Einfacher Kreis mit "G"
    # Zeichne einen weißen Kreis
    padding = 10
    circle_bbox = [padding, padding, size-padding, size-padding]
    draw.ellipse(circle_bbox, fill=(255, 255, 255, 255))
    
    # Speichere das Badge-Icon
    output_path = os.path.join('static', 'img', 'pwa', 'badge-96.png')
    img.save(output_path, 'PNG')
    print(f"✅ Badge-Icon erstellt: {output_path}")
    
    # Erstelle auch eine 72x72 Version
    img_72 = img.resize((72, 72), Image.Resampling.LANCZOS)
    output_path_72 = os.path.join('static', 'img', 'pwa', 'badge-72.png')
    img_72.save(output_path_72, 'PNG')
    print(f"✅ Badge-Icon erstellt: {output_path_72}")
    
    print()
    print("💡 Tipp: Für ein besseres Icon kannst du auch ein bestehendes Logo")
    print("   in ein monochromes Icon umwandeln mit einem Grafikprogramm.")
    print("   Das Badge-Icon sollte:")
    print("   - Nur weiß auf transparentem Hintergrund sein")
    print("   - Einfach und erkennbar sein")
    print("   - Die Silhouette deines Logos zeigen")

if __name__ == '__main__':
    try:
        create_badge_icon()
    except Exception as e:
        print(f"❌ Fehler: {e}")
        print("\nFallback: Verwende ein bestehendes Icon als Badge.")
        print("Bearbeite die Payload-Definitionen und verwende:")
        print("  'badge': '/static/img/pwa/icon-96.png'")

