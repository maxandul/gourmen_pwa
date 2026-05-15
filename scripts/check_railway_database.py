#!/usr/bin/env python3
"""
Railway Database Check Script
Überprüft alle Tabellen und deren Struktur in der Railway-Datenbank
"""

import os
import sys
from flask import Flask
from sqlalchemy import text, inspect

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

def check_database():
    """Überprüft die Datenbankstruktur"""
    app = create_app('production')
    
    with app.app_context():
        from backend.extensions import db
        
        inspector = inspect(db.engine)
        
        print("\n" + "="*80)
        print("🔍 RAILWAY DATENBANK-ÜBERPRÜFUNG")
        print("="*80 + "\n")
        
        # 1. Liste aller Tabellen
        print("📋 VORHANDENE TABELLEN:")
        print("-" * 80)
        
        tables = inspector.get_table_names()
        
        for table_name in sorted(tables):
            columns = inspector.get_columns(table_name)
            print(f"\n✅ {table_name} ({len(columns)} Spalten)")
            
            # Zeige die wichtigsten Spalten
            for col in columns[:5]:  # Nur erste 5 Spalten
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                col_type = str(col['type'])
                print(f"   - {col['name']}: {col_type} {nullable}")
            
            if len(columns) > 5:
                print(f"   ... und {len(columns) - 5} weitere Spalten")
        
        print("\n" + "="*80)
        print(f"📊 ZUSAMMENFASSUNG: {len(tables)} Tabellen gefunden")
        print("="*80 + "\n")
        
        # 2. Erwartete Tabellen prüfen
        expected_tables = [
            'members',
            'member_sensitive',
            'member_mfa',
            'mfa_backup_codes',
            'events',
            'participations',
            'documents',
            'audit_events',
            'ratings',
            'push_subscriptions',
            'merch_articles_legacy',
            'merch_variants_legacy',
            'merch_orders_legacy',
            'merch_order_items_legacy',
            'merch_suppliers',
            'merch_articles',
            'merch_variants',
            'merch_rounds',
            'merch_round_items',
            'merch_orders',
            'merch_order_items',
        ]
        
        print("🔎 ERWARTETE TABELLEN:")
        print("-" * 80)
        
        missing_tables = []
        for expected in expected_tables:
            if expected in tables:
                print(f"✅ {expected}")
            else:
                print(f"❌ {expected} - FEHLT!")
                missing_tables.append(expected)
        
        if missing_tables:
            print("\n⚠️  FEHLENDE TABELLEN:")
            for missing in missing_tables:
                print(f"   - {missing}")
        else:
            print("\n✅ Alle erwarteten Tabellen sind vorhanden!")
        
        # 3. Foreign Keys prüfen
        print("\n" + "="*80)
        print("🔗 FOREIGN KEY CONSTRAINTS (Auswahl):")
        print("-" * 80)
        
        important_fks = [
            'merch_variants_legacy',
            'merch_orders_legacy',
            'merch_order_items_legacy',
            'merch_variants',
            'merch_orders',
            'merch_order_items',
            'merch_round_items',
            'participations',
            'documents',
            'ratings',
        ]
        
        for table in important_fks:
            if table in tables:
                fks = inspector.get_foreign_keys(table)
                if fks:
                    print(f"\n{table}:")
                    for fk in fks:
                        print(f"   - {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
        
        # 4. Indizes prüfen
        print("\n" + "="*80)
        print("📑 WICHTIGE INDIZES:")
        print("-" * 80)
        
        for table in [
            'merch_orders_legacy',
            'merch_order_items_legacy',
            'merch_variants_legacy',
            'merch_orders',
            'merch_order_items',
            'merch_variants',
        ]:
            if table in tables:
                indexes = inspector.get_indexes(table)
                if indexes:
                    print(f"\n{table}:")
                    for idx in indexes:
                        cols = ', '.join(idx['column_names'])
                        unique = " (UNIQUE)" if idx.get('unique') else ""
                        print(f"   - {idx['name']}: {cols}{unique}")
        
        print("\n" + "="*80)
        print("✅ DATENBANKPRÜFUNG ABGESCHLOSSEN")
        print("="*80 + "\n")

if __name__ == '__main__':
    check_database()

