#!/usr/bin/env python3
"""
Verkleinert die bestehenden Badge-Icons auf die richtige Größe
"""

from PIL import Image
import os

def resize_badge_icons():
    """Verkleinert badge-72.png auf 72x72 und badge-96.png auf 96x96"""
    
    # Pfade zu den Badge-Icons
    badge_72_path = os.path.join('static', 'img', 'pwa', 'badge-72.png')
    badge_96_path = os.path.join('static', 'img', 'pwa', 'badge-96.png')
    
    # Badge-72 auf 72x72 verkleinern
    if os.path.exists(badge_72_path):
        img_72 = Image.open(badge_72_path)
        print(f"badge-72.png - Aktuelle Größe: {img_72.size}")
        img_72_resized = img_72.resize((72, 72), Image.Resampling.LANCZOS)
        img_72_resized.save(badge_72_path, 'PNG', optimize=True)
        print(f"✅ badge-72.png verkleinert auf: 72x72")
    else:
        print(f"❌ {badge_72_path} nicht gefunden")
    
    # Badge-96 auf 96x96 verkleinern
    if os.path.exists(badge_96_path):
        img_96 = Image.open(badge_96_path)
        print(f"badge-96.png - Aktuelle Größe: {img_96.size}")
        img_96_resized = img_96.resize((96, 96), Image.Resampling.LANCZOS)
        img_96_resized.save(badge_96_path, 'PNG', optimize=True)
        print(f"✅ badge-96.png verkleinert auf: 96x96")
    else:
        print(f"❌ {badge_96_path} nicht gefunden")

if __name__ == '__main__':
    try:
        resize_badge_icons()
        print("\n🎉 Fertig! Die Badge-Icons haben jetzt die richtige Größe.")
    except Exception as e:
        print(f"❌ Fehler: {e}")

