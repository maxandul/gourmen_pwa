#!/usr/bin/env python3
"""
Script to fix push_subscriptions table schema on Railway
Adds missing columns if they don't exist
"""

import os
import sys
from datetime import date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db

def fix_push_subscriptions_table():
    """Fix the push_subscriptions table schema"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Fixing push_subscriptions table schema...")
            
            # Check if table exists
            result = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'push_subscriptions'
                );
            """)).fetchone()
            
            if not result[0]:
                print("❌ Table push_subscriptions does not exist!")
                return False
            
            print("✅ Table push_subscriptions exists")
            
            # Check existing columns
            columns_result = db.session.execute(db.text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'push_subscriptions'
                ORDER BY ordinal_position;
            """)).fetchall()
            
            existing_columns = [row[0] for row in columns_result]
            print(f"📋 Existing columns: {existing_columns}")
            
            # Add missing columns
            columns_to_add = [
                ('created_at', 'DATE', True),
                ('updated_at', 'DATE', True), 
                ('last_used_at', 'DATE', False)
            ]
            
            for column_name, data_type, is_nullable in columns_to_add:
                if column_name not in existing_columns:
                    print(f"➕ Adding column: {column_name}")
                    
                    # Add column without NOT NULL constraint first
                    db.session.execute(db.text(f"""
                        ALTER TABLE push_subscriptions 
                        ADD COLUMN {column_name} {data_type};
                    """))
                    
                    # Fill existing rows with current date if not nullable
                    if not is_nullable:
                        db.session.execute(db.text(f"""
                            UPDATE push_subscriptions 
                            SET {column_name} = CURRENT_DATE 
                            WHERE {column_name} IS NULL;
                        """))
                        
                        # Add NOT NULL constraint
                        db.session.execute(db.text(f"""
                            ALTER TABLE push_subscriptions 
                            ALTER COLUMN {column_name} SET NOT NULL;
                        """))
                        
                        # Add default value for future inserts
                        db.session.execute(db.text(f"""
                            ALTER TABLE push_subscriptions 
                            ALTER COLUMN {column_name} SET DEFAULT CURRENT_DATE;
                        """))
                    
                    print(f"✅ Column {column_name} added successfully")
                else:
                    print(f"⏭️ Column {column_name} already exists")
            
            # Commit changes
            db.session.commit()
            print("🎉 Database schema fixed successfully!")
            
            # Verify final schema
            final_columns = db.session.execute(db.text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'push_subscriptions'
                ORDER BY ordinal_position;
            """)).fetchall()
            
            print("\n📋 Final table schema:")
            for row in final_columns:
                print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing database schema: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting push_subscriptions table fix...")
    success = fix_push_subscriptions_table()
    
    if success:
        print("\n✅ Database schema fix completed successfully!")
        print("🔄 Now restart your Railway app to test the fix.")
    else:
        print("\n❌ Database schema fix failed!")
        sys.exit(1)
