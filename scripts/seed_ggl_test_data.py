#!/usr/bin/env python3
"""
GGL Test Data Seeder für 2025
Erstellt spezifische Testdaten für das GGL Chart
"""

import os
import sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import random

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.event import Event, EventType
from backend.models.participation import Participation, Esstyp
from backend.services.ggl_rules import GGLService

def get_second_friday_of_month(year, month):
    """Calculate second Friday of the month"""
    first_day = date(year, month, 1)
    days_to_friday = (4 - first_day.weekday()) % 7
    first_friday = first_day + relativedelta(days=days_to_friday)
    second_friday = first_friday + relativedelta(days=7)
    return second_friday

def create_ggl_test_events_2025():
    """Create specific test events for 2025 GGL testing"""
    print("📅 Erstelle GGL Test-Events für 2025...")
    
    # Get all members
    members = Member.query.filter_by(is_active=True).all()
    if len(members) < 11:
        print("❌ Nicht genügend Mitglieder vorhanden. Bitte zuerst seed_test_data.py ausführen.")
        return []
    
    # Create 3 events for 2025
    events = []
    
    # Event 1: Januar 2025 (alle teilnehmen)
    jan_event = create_event_with_participations(
        year=2025, month=1,
        restaurant="Restaurant Adler",
        kueche="Schweizer Küche",
        members=members,
        participating_members=members,  # Alle teilnehmen
        bill_amount_chf=280
    )
    events.append(jan_event)
    
    # Event 2: Februar 2025 (nur 8 von 11 teilnehmen)
    feb_participants = random.sample(members, k=8)
    feb_event = create_event_with_participations(
        year=2025, month=2,
        restaurant="Ristorante Milano", 
        kueche="Italienisch",
        members=members,
        participating_members=feb_participants,  # Nur 8 teilnehmen
        bill_amount_chf=320
    )
    events.append(feb_event)
    
    # Event 3: März 2025 (alle teilnehmen)
    mar_event = create_event_with_participations(
        year=2025, month=3,
        restaurant="Sushi Yamato",
        kueche="Japanisch", 
        members=members,
        participating_members=members,  # Alle teilnehmen
        bill_amount_chf=250
    )
    events.append(mar_event)
    
    db.session.commit()
    return events

def create_event_with_participations(year, month, restaurant, kueche, members, participating_members, bill_amount_chf):
    """Create an event with specific participations"""
    event_date = get_second_friday_of_month(year, month)
    organizer = random.choice(participating_members)
    
    event = Event(
        datum=datetime.combine(event_date, datetime.min.time().replace(hour=19)),
        event_typ=EventType.MONATSESSEN,
        organisator_id=organizer.id,
        restaurant=restaurant,
        kueche=kueche,
        season=year,
        published=True,
        rechnungsbetrag_rappen=bill_amount_chf * 100
    )
    
    # 7% Trinkgeld, aufgerundet auf 10er
    tip_amount = int(bill_amount_chf * 0.07 * 100)
    total_amount = event.rechnungsbetrag_rappen + tip_amount
    event.gesamtbetrag_rappen = ((total_amount + 999) // 1000) * 1000
    event.trinkgeld_rappen = event.gesamtbetrag_rappen - event.rechnungsbetrag_rappen
    
    # BillBro weights
    event.betrag_sparsam_rappen = int(event.gesamtbetrag_rappen * 0.7 / 3)
    event.betrag_normal_rappen = int(event.gesamtbetrag_rappen * 1.0 / 3)
    event.betrag_allin_rappen = int(event.gesamtbetrag_rappen * 1.3 / 3)
    
    db.session.add(event)
    db.session.flush()  # Get event ID
    
    # Create participations
    for member in members:
        teilnahme = member in participating_members
        
        participation = Participation(
            member_id=member.id,
            event_id=event.id,
            teilnahme=teilnahme,
            responded_at=datetime.utcnow() - timedelta(days=random.randint(1, 7))
        )
        
        # BillBro-Daten nur für teilnehmende Members
        if teilnahme:
            # Zufällige Esstyp-Verteilung
            esstyp_choices = [Esstyp.SPARSAM, Esstyp.NORMAL, Esstyp.ALLIN]
            esstyp_weights = [0.2, 0.6, 0.2]
            participation.esstyp = random.choices(esstyp_choices, weights=esstyp_weights)[0]
            
            # Realistische Schätzungen
            actual_amount_chf = event.rechnungsbetrag_rappen / 100
            guess_factor = random.uniform(0.7, 1.3)
            guess_chf = int(actual_amount_chf * guess_factor)
            participation.guess_bill_amount_rappen = guess_chf * 100
            
            # Differenz berechnen
            participation.diff_amount_rappen = abs(
                participation.guess_bill_amount_rappen - event.rechnungsbetrag_rappen
            )
            
            # Share berechnen
            if participation.esstyp == Esstyp.SPARSAM:
                participation.calculated_share_rappen = event.betrag_sparsam_rappen
            elif participation.esstyp == Esstyp.NORMAL:
                participation.calculated_share_rappen = event.betrag_normal_rappen
            elif participation.esstyp == Esstyp.ALLIN:
                participation.calculated_share_rappen = event.betrag_allin_rappen
        
        db.session.add(participation)
    
    # Calculate GGL points
    db.session.flush()
    GGLService.calculate_event_points(event.id)
    
    print(f"  ✅ {event_date.strftime('%d.%m.%Y')} - {restaurant} ({len(participating_members)}/{len(members)} Teilnehmer)")
    return event

def main():
    """Main seeding function"""
    print("🎯 GGL Test-Daten Seeder für 2025")
    print("=" * 40)
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        print("🗄️  Verbinde mit Datenbank...")
        
        # Check if members exist
        members = Member.query.filter_by(is_active=True).all()
        if len(members) < 11:
            print("❌ Nicht genügend Mitglieder vorhanden.")
            print("   Bitte zuerst 'python scripts/seed_test_data.py' ausführen.")
            return
        
        # Check if 2025 events already exist
        existing_events = Event.query.filter_by(season=2025).count()
        if existing_events > 0:
            print(f"⚠️  {existing_events} Events für 2025 bereits vorhanden")
            response = input("Trotzdem fortfahren? (j/N): ")
            if response.lower() not in ['j', 'ja', 'y', 'yes']:
                print("❌ Abgebrochen")
                return
        
        try:
            # Create test events
            events = create_ggl_test_events_2025()
            
            print(f"\n✅ GGL Test-Daten erfolgreich erstellt!")
            print(f"   📅 {len(events)} Events für 2025")
            print(f"   🎯 GGL-Punkte berechnet")
            
            print(f"\n📊 Test-Szenarien:")
            print(f"   • Event 1 (Jan): Alle 11 Mitglieder teilnehmen")
            print(f"   • Event 2 (Feb): Nur 8 von 11 Mitgliedern teilnehmen")
            print(f"   • Event 3 (Mär): Alle 11 Mitglieder teilnehmen")
            print(f"   • 3 Mitglieder haben Lücken in der Teilnahme")
            print(f"   • 1 Mitglied hat noch nie teilgenommen (falls vorhanden)")
            
        except Exception as e:
            print(f"❌ Fehler beim Seeding: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()
