#!/usr/bin/env python3
"""
VAPID Key Base64 Encoder
Encodiert den VAPID Private Key in Base64 für Railway
"""

import base64
from pathlib import Path


def main():
    # Versuche den private key aus der Datei zu lesen
    vapid_private_file = Path('vapid_private.pem')
    
    if not vapid_private_file.exists():
        print("❌ Fehler: vapid_private.pem nicht gefunden!")
        print("   Bitte führe zuerst aus: python scripts/generate_vapid_keys.py")
        return
    
    # Lies den PEM Key
    with open(vapid_private_file, 'r', encoding='utf-8') as f:
        pem_key = f.read()
    
    # Encodiere in Base64
    encoded_key = base64.b64encode(pem_key.encode('utf-8')).decode('ascii')
    
    print("=" * 80)
    print("VAPID Private Key - Base64 Format für Railway")
    print("=" * 80)
    print()
    print("Kopiere den folgenden String und füge ihn in Railway als")
    print("Umgebungsvariable VAPID_PRIVATE_KEY ein:")
    print()
    print("-" * 80)
    print(encoded_key)
    print("-" * 80)
    print()
    print("✅ Dieser Base64-String enthält den kompletten PEM-Key ohne Newline-Probleme")
    print()
    
    # Auch den Public Key anzeigen
    vapid_public_file = Path('vapid_public.txt')
    if vapid_public_file.exists():
        with open(vapid_public_file, 'r', encoding='utf-8') as f:
            public_key = f.read().strip()
        
        print("=" * 80)
        print("VAPID Public Key für Railway")
        print("=" * 80)
        print()
        print("VAPID_PUBLIC_KEY:")
        print("-" * 80)
        print(public_key)
        print("-" * 80)
        print()


if __name__ == '__main__':
    main()

