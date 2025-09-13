#!/usr/bin/env python3
"""
Script zum Generieren von VAPID-Keys für Railway Deployment
Führe dieses Script lokal aus und kopiere die Keys nach Railway
"""

import sys
import os

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.services.vapid_service import VAPIDService

def main():
    print("🔑 Generiere VAPID-Keys für Railway...")
    
    # Generiere Keys
    keys = VAPIDService.generate_vapid_keys()
    
    print("\n" + "="*60)
    print("RAILWAY ENVIRONMENT VARIABLES:")
    print("="*60)
    print(f"VAPID_PUBLIC_KEY={keys['public_key']}")
    print("\n" + "="*60)
    print("VAPID_PRIVATE_KEY:")
    print("="*60)
    print(keys['private_key'])
    print("="*60)
    
    print("\n📋 Anweisungen:")
    print("1. Kopiere die VAPID_PUBLIC_KEY in Railway Environment Variables")
    print("2. Kopiere den kompletten VAPID_PRIVATE_KEY (inkl. -----BEGIN/END-----)")
    print("3. Füge beide als Environment Variables in Railway hinzu")
    print("4. Restart deine Railway App")
    
    print(f"\n🔍 Public Key (für Client): {keys['public_key'][:50]}...")
    print(f"🔐 Private Key (für Server): {keys['private_key'][:50]}...")

if __name__ == "__main__":
    main()

