#!/usr/bin/env python3
"""
Test App Database Integration
"""

import os
import sys

def test_app_database():
    """Teste App-Datenbank-Integration"""
    print("=== APP DATABASE INTEGRATION TEST ===")
    
    try:
        # Füge Backend zum Pfad hinzu
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        
        print("1. Creating Flask app...")
        from backend.app import create_app
        app = create_app('production')
        print("✓ Flask app created")
        
        print("2. Testing app context...")
        with app.app_context():
            print("✓ App context works")
            
            print("3. Testing model imports...")
            from backend.models.member import Member
            from backend.models.event import Event
            from backend.models.participation import Participation
            print("✓ Models imported")
            
            print("4. Testing database queries...")
            
            # Teste Member query
            try:
                member_count = Member.query.count()
                print(f"✓ Member query successful: {member_count} members")
            except Exception as e:
                print(f"❌ Member query failed: {e}")
                return False
            
            # Teste Event query
            try:
                event_count = Event.query.count()
                print(f"✓ Event query successful: {event_count} events")
            except Exception as e:
                print(f"❌ Event query failed: {e}")
                return False
            
            # Teste Participation query
            try:
                participation_count = Participation.query.count()
                print(f"✓ Participation query successful: {participation_count} participations")
            except Exception as e:
                print(f"❌ Participation query failed: {e}")
                return False
            
            print("5. Testing health endpoint...")
            with app.test_client() as client:
                response = client.get('/health')
                if response.status_code == 200:
                    print("✓ Health endpoint works")
                else:
                    print(f"❌ Health endpoint failed: {response.status_code}")
                    return False
        
        print("\n✅ All database integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ App database integration test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_app_database()
    sys.exit(0 if success else 1)
