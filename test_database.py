#!/usr/bin/env python3
"""
Datenbank-Test Script für Railway
"""

import os
import sys
import psycopg
from urllib.parse import urlparse

def test_database():
    """Teste Datenbankverbindung und Tabellen"""
    print("=== DATABASE TEST ===")
    
    try:
        # Hole DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not set")
            return False
        
        print(f"✓ DATABASE_URL found: {database_url[:50]}...")
        
        # Für lokale Tests: Verwende öffentliche Verbindung
        if 'railway.internal' in database_url:
            print("⚠ Using internal Railway URL - switching to public connection")
            # Ersetze interne URL mit öffentlicher
            database_url = database_url.replace('postgres.railway.internal:5432', 'tramway.proxy.rlwy.net:16677')
            print(f"✓ Using public URL: {database_url[:50]}...")
        
        # Parse DATABASE_URL
        parsed = urlparse(database_url)
        print(f"Host: {parsed.hostname}")
        print(f"Port: {parsed.port}")
        print(f"Database: {parsed.path[1:]}")
        
        # Verbinde zur Datenbank
        print("Connecting to database...")
        conn = psycopg.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path[1:]
        )
        print("✓ Database connection successful")
        
        # Teste einfache Abfrage
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            print(f"✓ Simple query result: {result}")
        
        # Liste alle Tabellen
        print("\n=== EXISTING TABLES ===")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            if tables:
                print("✓ Found tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("⚠ No tables found")
        
        # Teste push_subscriptions Tabelle spezifisch
        print("\n=== PUSH_SUBSCRIPTIONS TABLE ===")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'push_subscriptions' 
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            
            if columns:
                print("✓ push_subscriptions table exists with columns:")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}, nullable: {col[2]})")
            else:
                print("⚠ push_subscriptions table not found")
        
        # Teste andere wichtige Tabellen
        important_tables = ['member', 'event', 'participation', 'audit_event']
        print("\n=== IMPORTANT TABLES CHECK ===")
        with conn.cursor() as cur:
            for table in important_tables:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = %s AND table_schema = 'public';
                """, (table,))
                count = cur.fetchone()[0]
                if count > 0:
                    print(f"✓ {table} table exists")
                else:
                    print(f"❌ {table} table missing")
        
        conn.close()
        print("\n✅ Database test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_database()
    sys.exit(0 if success else 1)
