#!/usr/bin/env python3
"""
Create a test user for first login password change testing
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Role

def main():
    """Create test user"""
    print("👤 Erstelle Test-User für erste Anmeldung...")
    
    app = create_app('development')
    
    with app.app_context():
        # Check if test user already exists
        test_email = "test.firstlogin@gourmen.ch"
        existing_user = Member.query.filter_by(email=test_email).first()
        
        if existing_user:
            print(f"⚠️  Test-User {test_email} bereits vorhanden")
            # Reset password_changed_at to None for testing
            existing_user.password_changed_at = None
            db.session.commit()
            print(f"✅ password_changed_at für {test_email} zurückgesetzt")
            return
        
        # Create new test user
        test_user = Member(
            email=test_email,
            vorname="Test",
            nachname="FirstLogin",
            role=Role.MEMBER,
            is_active=True,
            password_changed_at=None  # This will trigger first login password change
        )
        test_user.set_password("Test123!")
        
        # Reset password_changed_at to None (since set_password sets it)
        test_user.password_changed_at = None
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✅ Test-User erstellt: {test_email}")
        print(f"   Passwort: Test123!")
        print(f"   password_changed_at: {test_user.password_changed_at}")
        print(f"   Bei der ersten Anmeldung wird zur Passwort-Änderung weitergeleitet")

if __name__ == "__main__":
    main()
