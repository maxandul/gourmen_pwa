#!/usr/bin/env python3
"""
Update existing members with password_changed_at timestamp
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member

def main():
    """Update existing members"""
    print("🔄 Update bestehende Member mit password_changed_at...")
    
    app = create_app('development')
    
    with app.app_context():
        # Get all members without password_changed_at
        members = Member.query.filter_by(password_changed_at=None).all()
        
        if not members:
            print("✅ Alle Member haben bereits password_changed_at gesetzt")
            return
        
        print(f"📝 Update {len(members)} Member...")
        
        for member in members:
            # Set password_changed_at to created_at if available, otherwise now
            member.password_changed_at = member.created_at or datetime.utcnow()
            print(f"  ✅ {member.email}: {member.password_changed_at}")
        
        db.session.commit()
        print(f"✅ {len(members)} Member erfolgreich aktualisiert!")

if __name__ == "__main__":
    main()
