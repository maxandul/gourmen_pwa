#!/usr/bin/env python3
"""
Spirit Animals für alle Mitglieder zuweisen
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member

def assign_spirit_animals():
    """Assign spirit animals to all members"""
    print("🦁 Weise Spirit Animals zu...")
    
    spirit_animals = [
        "🦁", "🦅", "🐺", "🐻", "🦈", "🐅", "🦊", "🦉", "🐼", "🐬", "🐘"
    ]
    
    members = Member.query.filter_by(is_active=True).all()
    
    for i, member in enumerate(members):
        if not member.spirit_animal or member.spirit_animal == "":
            member.spirit_animal = spirit_animals[i % len(spirit_animals)]
            print(f"  ✅ {member.display_name} → {member.spirit_animal}")
        else:
            print(f"  ⚠️  {member.display_name} hat bereits {member.spirit_animal}")
    
    db.session.commit()
    print(f"\n✅ {len(members)} Mitglieder bearbeitet")

def main():
    """Main function"""
    print("🦁 Spirit Animals Zuweiser")
    print("=" * 30)
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        print("🗄️  Verbinde mit Datenbank...")
        
        try:
            assign_spirit_animals()
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()
