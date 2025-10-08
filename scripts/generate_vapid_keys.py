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
    
    # Private Key mit \n statt echten Newlines für Railway
    private_key_escaped = keys['private_key'].replace('\n', '\\n')
    
    print("\n" + "="*80)
    print("📋 RAILWAY ENVIRONMENT VARIABLES - KOPIERE DIESE EXAKT:")
    print("="*80)
    
    print("\n🔑 VAPID_PUBLIC_KEY:")
    print("-" * 80)
    print(keys['public_key'])
    print("-" * 80)
    
    print("\n🔐 VAPID_PRIVATE_KEY (WICHTIG: Als EINE Zeile mit \\n):")
    print("-" * 80)
    print(private_key_escaped)
    print("-" * 80)
    
    print("\n" + "="*80)
    print("📝 ANWEISUNGEN:")
    print("="*80)
    print("1. Gehe zu Railway → deinem Projekt → Variables")
    print("2. Lösche die existierenden VAPID_PUBLIC_KEY und VAPID_PRIVATE_KEY")
    print("3. Erstelle neue Variables:")
    print("   - Name: VAPID_PUBLIC_KEY")
    print("     Wert: [Kopiere den Public Key von oben - EINE Zeile, KEIN \\n]")
    print("   - Name: VAPID_PRIVATE_KEY")
    print("     Wert: [Kopiere den Private Key von oben - EINE Zeile, MIT \\n]")
    print("4. Railway wird automatisch neu deployen")
    print("5. Teste nach ~2 Min mit 'Test-Push senden' in der App")
    print("="*80)

if __name__ == "__main__":
    main()

