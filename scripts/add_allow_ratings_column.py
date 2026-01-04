#!/usr/bin/env python3
"""
Fügt die allow_ratings Spalte zur events Tabelle hinzu
"""

import os
import sys
import sqlite3

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_allow_ratings_column():
    """Fügt die allow_ratings Spalte zur events Tabelle hinzu"""
    
    # Pfad zur Datenbank
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'gourmen_dev.db')
    
    if not os.path.exists(db_path):
        print(f"[FEHLER] Datenbank nicht gefunden: {db_path}")
        print("         Bitte stelle sicher, dass die Datenbank existiert.")
        return False
    
    print(f"[INFO] Verwende Datenbank: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe ob events Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if not cursor.fetchone():
            print("[FEHLER] Tabelle 'events' existiert nicht in der Datenbank")
            conn.close()
            return False
        
        # Prüfe aktuelle Spalten
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"\n[INFO] Gefundene Spalten in events Tabelle ({len(column_names)}):")
        for col in columns:
            print(f"       - {col[1]} ({col[2]})")
        
        # Prüfe ob allow_ratings bereits existiert
        if 'allow_ratings' in column_names:
            print("\n[OK] Spalte 'allow_ratings' existiert bereits!")
            conn.close()
            return True
        
        # Füge die Spalte hinzu
        print("\n[INFO] Fuege Spalte 'allow_ratings' hinzu...")
        cursor.execute("ALTER TABLE events ADD COLUMN allow_ratings BOOLEAN DEFAULT 1 NOT NULL")
        conn.commit()
        
        # Verifiziere
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'allow_ratings' in column_names:
            print("[OK] Spalte 'allow_ratings' erfolgreich hinzugefuegt!")
            print(f"\n[INFO] Neue Spaltenliste ({len(column_names)} Spalten):")
            for col in columns:
                if col[1] == 'allow_ratings':
                    print(f"       - {col[1]} ({col[2]}) <- NEU")
                else:
                    print(f"       - {col[1]} ({col[2]})")
            conn.close()
            return True
        else:
            print("[FEHLER] Spalte wurde nicht hinzugefuegt")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"[FEHLER] Datenbankfehler: {e}")
        return False
    except Exception as e:
        print(f"[FEHLER] {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("  Gourmen - Add allow_ratings Column")
    print("=" * 60)
    success = add_allow_ratings_column()
    print("=" * 60)
    sys.exit(0 if success else 1)

