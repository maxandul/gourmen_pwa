#!/usr/bin/env python3
"""
Railway Database Schema Validation
Vergleicht die tatsächliche Datenbankstruktur mit den erwarteten Models
"""

import os
import sys
from sqlalchemy import inspect

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

# Erwartete Tabellen-Struktur basierend auf den Models
EXPECTED_SCHEMA = {
    'members': {
        'id', 'email', 'vorname', 'nachname', 'role', 'is_active', 
        'password_hash', 'password_changed_at', 'spirit_animal', 
        'created_at', 'updated_at'
    },
    'member_sensitive': {
        'id', 'member_id', 'telefon_encrypted', 'adresse_encrypted', 
        'geburtsdatum_encrypted', 'allergien_encrypted', 'created_at', 'updated_at'
    },
    'member_mfa': {
        'id', 'member_id', 'totp_secret_encrypted', 'is_enabled', 
        'created_at', 'updated_at'
    },
    'mfa_backup_codes': {
        'id', 'member_id', 'code_hash', 'is_used', 'used_at', 'created_at'
    },
    'events': {
        'id', 'name', 'date', 'event_type', 'location', 'description', 
        'max_participants', 'deadline', 'price_rappen', 'place_id', 
        'place_details', 'created_at', 'updated_at'
    },
    'participations': {
        'id', 'event_id', 'member_id', 'status', 'guest_count', 
        'guest_names', 'notes', 'created_at', 'updated_at'
    },
    'documents': {
        'id', 'event_id', 'filename', 'file_path', 'file_type', 
        'file_size', 'uploaded_by', 'created_at'
    },
    'audit_events': {
        'id', 'event_type', 'user_id', 'target_type', 'target_id', 
        'details', 'ip_address', 'user_agent', 'created_at'
    },
    'event_ratings': {
        'id', 'event_id', 'member_id', 'location_rating', 'food_rating', 
        'atmosphere_rating', 'value_rating', 'comment', 'created_at', 'updated_at'
    },
    'push_subscriptions': {
        'id', 'member_id', 'endpoint', 'p256dh_key', 'auth_key', 
        'user_agent', 'created_at', 'updated_at'
    },
    'merch_articles': {
        'id', 'name', 'description', 'base_supplier_price_rappen', 
        'base_member_price_rappen', 'image_url', 'is_active', 
        'created_at', 'updated_at'
    },
    'merch_variants': {
        'id', 'article_id', 'color', 'size', 'supplier_price_rappen', 
        'member_price_rappen', 'is_active', 'created_at', 'updated_at'
    },
    'merch_orders': {
        'id', 'member_id', 'order_number', 'status', 'total_member_price_rappen', 
        'total_supplier_price_rappen', 'total_profit_rappen', 'notes', 
        'created_at', 'updated_at', 'delivered_at'
    },
    'merch_order_items': {
        'id', 'order_id', 'article_id', 'variant_id', 'quantity', 
        'unit_member_price_rappen', 'unit_supplier_price_rappen', 
        'total_member_price_rappen', 'total_supplier_price_rappen', 
        'total_profit_rappen', 'created_at'
    }
}

def validate_database():
    """Validiert die Datenbankstruktur gegen erwartete Schema"""
    app = create_app('production')
    
    with app.app_context():
        from backend.extensions import db
        
        inspector = inspect(db.engine)
        actual_tables = inspector.get_table_names()
        
        print("\n" + "="*100)
        print("🔍 DETAILLIERTE RAILWAY DATENBANK-VALIDIERUNG")
        print("="*100 + "\n")
        
        all_ok = True
        missing_tables = []
        missing_columns = {}
        extra_columns = {}
        
        # Prüfe jede erwartete Tabelle
        for table_name, expected_columns in EXPECTED_SCHEMA.items():
            print(f"\n{'─'*100}")
            print(f"📋 Tabelle: {table_name}")
            print(f"{'─'*100}")
            
            if table_name not in actual_tables:
                print(f"❌ FEHLT KOMPLETT!")
                missing_tables.append(table_name)
                all_ok = False
                continue
            
            # Hole tatsächliche Spalten
            actual_cols = inspector.get_columns(table_name)
            actual_col_names = {col['name'] for col in actual_cols}
            
            # Prüfe fehlende Spalten
            missing = expected_columns - actual_col_names
            if missing:
                missing_columns[table_name] = missing
                all_ok = False
                print(f"❌ FEHLENDE SPALTEN: {', '.join(sorted(missing))}")
            
            # Prüfe extra Spalten (nicht unbedingt ein Fehler)
            extra = actual_col_names - expected_columns
            if extra:
                extra_columns[table_name] = extra
                print(f"ℹ️  ZUSÄTZLICHE SPALTEN: {', '.join(sorted(extra))}")
            
            # Zeige alle vorhandenen Spalten mit Details
            if not missing:
                print(f"✅ Alle {len(expected_columns)} erwarteten Spalten vorhanden")
            
            print(f"\n   Spalten-Details:")
            for col in sorted(actual_cols, key=lambda x: x['name']):
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                col_type = str(col['type'])
                status = "✅" if col['name'] in expected_columns else "ℹ️ "
                
                # Kürze lange Typen
                if len(col_type) > 30:
                    col_type = col_type[:27] + "..."
                
                print(f"   {status} {col['name']:<30} {col_type:<25} {nullable}")
        
        # Prüfe auf unerwartete Tabellen
        print(f"\n{'='*100}")
        print("📊 ZUSAMMENFASSUNG")
        print(f"{'='*100}\n")
        
        unexpected_tables = set(actual_tables) - set(EXPECTED_SCHEMA.keys())
        
        print(f"Erwartete Tabellen: {len(EXPECTED_SCHEMA)}")
        print(f"Gefundene Tabellen: {len(actual_tables)}")
        
        if missing_tables:
            print(f"\n❌ FEHLENDE TABELLEN ({len(missing_tables)}):")
            for table in missing_tables:
                print(f"   - {table}")
        
        if unexpected_tables:
            print(f"\nℹ️  UNERWARTETE TABELLEN ({len(unexpected_tables)}):")
            for table in unexpected_tables:
                print(f"   - {table}")
        
        if missing_columns:
            print(f"\n❌ TABELLEN MIT FEHLENDEN SPALTEN ({len(missing_columns)}):")
            for table, cols in missing_columns.items():
                print(f"   {table}: {', '.join(sorted(cols))}")
        
        # Foreign Keys Prüfung
        print(f"\n{'='*100}")
        print("🔗 FOREIGN KEY CONSTRAINTS")
        print(f"{'='*100}\n")
        
        expected_fks = {
            'member_sensitive': [('member_id', 'members')],
            'member_mfa': [('member_id', 'members')],
            'mfa_backup_codes': [('member_id', 'members')],
            'participations': [('event_id', 'events'), ('member_id', 'members')],
            'documents': [('event_id', 'events'), ('uploaded_by', 'members')],
            'event_ratings': [('event_id', 'events'), ('member_id', 'members')],
            'push_subscriptions': [('member_id', 'members')],
            'merch_variants': [('article_id', 'merch_articles')],
            'merch_orders': [('member_id', 'members')],
            'merch_order_items': [
                ('order_id', 'merch_orders'),
                ('article_id', 'merch_articles'),
                ('variant_id', 'merch_variants')
            ]
        }
        
        for table, expected_fk_list in expected_fks.items():
            if table not in actual_tables:
                continue
                
            actual_fks = inspector.get_foreign_keys(table)
            actual_fk_map = {
                tuple(fk['constrained_columns'])[0]: fk['referred_table']
                for fk in actual_fks
            }
            
            print(f"\n{table}:")
            for col, ref_table in expected_fk_list:
                if col in actual_fk_map and actual_fk_map[col] == ref_table:
                    print(f"   ✅ {col} → {ref_table}")
                else:
                    print(f"   ❌ {col} → {ref_table} (FEHLT oder FALSCH)")
                    all_ok = False
        
        # Finale Bewertung
        print(f"\n{'='*100}")
        if all_ok and not missing_tables and not missing_columns:
            print("✅ DATENBANK-SCHEMA VOLLSTÄNDIG UND KORREKT!")
        else:
            print("⚠️  DATENBANK-SCHEMA HAT PROBLEME - SIEHE DETAILS OBEN")
        print(f"{'='*100}\n")
        
        return all_ok

if __name__ == '__main__':
    try:
        success = validate_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

