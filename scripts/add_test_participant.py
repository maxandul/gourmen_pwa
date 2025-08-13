#!/usr/bin/env python3
"""
Script to add current user as participant to Event 6 for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.member import Member

def add_test_participant():
    """Add current user as participant to Event 6"""
    app = create_app()
    
    with app.app_context():
        # Get Event 6
        event = Event.query.get(6)
        if not event:
            print("❌ Event 6 nicht gefunden!")
            return
        
        print(f"📅 Event gefunden: {event.event_typ.value} am {event.display_date}")
        
        # Get current user (assuming admin@gourmen.ch)
        user = Member.query.filter_by(email='admin@gourmen.ch').first()
        if not user:
            print("❌ Benutzer admin@gourmen.ch nicht gefunden!")
            return
        
        print(f"👤 Benutzer gefunden: {user.full_name}")
        
        # Check if participation already exists
        existing_participation = Participation.query.filter_by(
            event_id=6,
            member_id=user.id
        ).first()
        
        if existing_participation:
            if existing_participation.teilnahme:
                print("✅ Sie sind bereits als Teilnehmer für Event 6 eingetragen!")
            else:
                # Update to participating
                existing_participation.teilnahme = True
                db.session.commit()
                print("✅ Ihre Teilnahme für Event 6 wurde aktiviert!")
        else:
            # Create new participation
            participation = Participation(
                event_id=6,
                member_id=user.id,
                teilnahme=True
            )
            db.session.add(participation)
            db.session.commit()
            print("✅ Sie wurden als Teilnehmer für Event 6 hinzugefügt!")
        
        print(f"\n🎯 Sie können jetzt Event 6 bewerten:")
        print(f"   - Gehen Sie zu: /events/6")
        print(f"   - Klicken Sie auf 'Event bewerten'")

if __name__ == '__main__':
    add_test_participant()
