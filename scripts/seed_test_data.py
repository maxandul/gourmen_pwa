#!/usr/bin/env python3
"""
Gourmen Test Data Seeder
Erstellt realistische Testdaten für die Gourmen-App
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

def create_test_members():
    """Create test members"""
    print("📝 Erstelle Test-Mitglieder...")
    
    members_data = [
        ("Max", "Müller", "max.mueller@gourmen.ch", Role.ADMIN),
        ("Lisa", "Weber", "lisa.weber@gourmen.ch", Role.MEMBER),
        ("Tom", "Schmidt", "tom.schmidt@gourmen.ch", Role.MEMBER),
        ("Anna", "Fischer", "anna.fischer@gourmen.ch", Role.MEMBER),
        ("David", "Meier", "david.meier@gourmen.ch", Role.MEMBER),
        ("Sarah", "Keller", "sarah.keller@gourmen.ch", Role.MEMBER),
        ("Marc", "Zimmermann", "marc.zimmermann@gourmen.ch", Role.MEMBER),
        ("Nina", "Hartmann", "nina.hartmann@gourmen.ch", Role.MEMBER),
        ("Felix", "Baumann", "felix.baumann@gourmen.ch", Role.MEMBER),
        ("Julia", "Wyss", "julia.wyss@gourmen.ch", Role.MEMBER),
        ("Reto", "Steiner", "reto.steiner@gourmen.ch", Role.MEMBER),
    ]
    
    created_members = []
    for vorname, nachname, email, role in members_data:
        # Check if member already exists
        existing = Member.query.filter_by(email=email).first()
        if existing:
            print(f"  ⚠️  {vorname} {nachname} bereits vorhanden")
            created_members.append(existing)
            continue
            
        member = Member(
            vorname=vorname,
            nachname=nachname,
            email=email,
            role=role,
            is_active=True
        )
        member.set_password("Test123!")  # Einfaches Test-Passwort
        db.session.add(member)
        created_members.append(member)
        print(f"  ✅ {vorname} {nachname} ({role.value})")
    
    db.session.commit()
    return created_members

def create_test_events(members):
    """Create test events for current and past year"""
    print("\n📅 Erstelle Test-Events...")
    
    current_year = datetime.now().year
    
    # Events für letztes Jahr (abgeschlossen)
    past_events = create_year_events(current_year - 1, members, completed=True)
    
    # Events für aktuelles Jahr (teilweise abgeschlossen)
    current_events = create_year_events(current_year, members, completed=False)
    
    db.session.commit()
    return past_events + current_events

def create_year_events(year, members, completed=False):
    """Create events for a specific year"""
    print(f"  📆 Jahr {year}...")
    events = []
    
    restaurants = [
        ("Restaurant Adler", "Schweizer Küche"),
        ("Ristorante Milano", "Italienisch"),
        ("Sushi Yamato", "Japanisch"),
        ("Brasserie Lyon", "Französisch"),
        ("Taverna Olympia", "Griechisch"),
        ("Zum Goldenen Hirschen", "Schweizer Küche"),
        ("Pizzeria Napoli", "Italienisch"),
        ("Restaurant Seeblick", "International"),
        ("Gasthaus Krone", "Traditionell"),
        ("Bistro Central", "Modern"),
        ("Restaurant Frohsinn", "Saisonal"),
        ("Trattoria Bella Vista", "Italienisch")
    ]
    
    # 12 Monatsessen
    for month in range(1, 13):
        event_date = get_second_friday_of_month(year, month)
        
        # Skip zukünftige Events wenn nicht completed
        if not completed and event_date > date.today():
            continue
            
        # Zufälliger Organisator
        organizer = random.choice(members)
        restaurant, cuisine = random.choice(restaurants)
        
        event = Event(
            datum=datetime.combine(event_date, datetime.min.time().replace(hour=19)),
            event_typ=EventType.MONATSESSEN,
            organisator_id=organizer.id,
            restaurant=restaurant,
            kueche=cuisine,
            website=f"https://{restaurant.lower().replace(' ', '-').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')}.ch",
            notizen=f"Reserviert für 8-10 Personen auf Namen {organizer.nachname}",
            season=year,
            published=True
        )
        
        # Für abgeschlossene Events: BillBro-Daten generieren
        if completed or event_date < date.today():
            # Rechnungsbetrag zwischen 180-350 CHF
            bill_amount_chf = random.randint(180, 350)
            event.rechnungsbetrag_rappen = bill_amount_chf * 100
            
            # 7% Trinkgeld, aufgerundet auf 10er
            tip_amount = int(bill_amount_chf * 0.07 * 100)
            total_amount = event.rechnungsbetrag_rappen + tip_amount
            event.gesamtbetrag_rappen = ((total_amount + 999) // 1000) * 1000
            event.trinkgeld_rappen = event.gesamtbetrag_rappen - event.rechnungsbetrag_rappen
            
            # BillBro weights (default)
            event.betrag_sparsam_rappen = int(event.gesamtbetrag_rappen * 0.7 / 3)
            event.betrag_normal_rappen = int(event.gesamtbetrag_rappen * 1.0 / 3)
            event.betrag_allin_rappen = int(event.gesamtbetrag_rappen * 1.3 / 3)
        
        db.session.add(event)
        events.append(event)
        
        # Teilnahmen generieren
        create_participations(event, members, completed or event_date < date.today())
        
        print(f"    ✅ {event_date.strftime('%d.%m.%Y')} - {restaurant} ({organizer.display_name})")
    
    # GV und Ausflug hinzufügen
    if completed or year < datetime.now().year:
        # Generalversammlung (März)
        gv_date = date(year, 3, 15)  # 15. März
        gv_organizer = members[0]  # Admin organisiert GV
        
        gv_event = Event(
            datum=datetime.combine(gv_date, datetime.min.time().replace(hour=19, minute=30)),
            event_typ=EventType.MONATSESSEN,
            organisator_id=gv_organizer.id,
            restaurant="Restaurant Rössli",
            kueche="Schweizer Küche",
            notizen="Generalversammlung - Start 19:30 Uhr",
            season=year,
            published=True
        )
        db.session.add(gv_event)
        create_participations(gv_event, members, True, participation_rate=0.9)  # Hohe Teilnahme
        events.append(gv_event)
        
        # Vereinsausflug (September)
        ausflug_date = date(year, 9, 12)  # Samstag im September
        ausflug_organizer = random.choice(members[1:])  # Nicht Admin
        
        ausflug_event = Event(
            datum=datetime.combine(ausflug_date, datetime.min.time().replace(hour=10)),
            event_typ=EventType.AUSFLUG,
            organisator_id=ausflug_organizer.id,
            restaurant="Bergrestaurant Alpenblick",
            kueche="Regional",
            notizen="Vereinsausflug - Treffpunkt 10:00 Uhr Bahnhof",
            season=year,
            published=True
        )
        db.session.add(ausflug_event)
        create_participations(ausflug_event, members, True, participation_rate=0.8)  # Gute Teilnahme
        events.append(ausflug_event)
        
        print(f"    ✅ GV & Ausflug hinzugefügt")
    
    return events

def create_participations(event, members, generate_billbro=False, participation_rate=0.7):
    """Create participations for an event"""
    # Zufällige Teilnahme (70% Standard, kann überschrieben werden)
    participating_members = random.sample(members, k=int(len(members) * participation_rate))
    
    for member in members:
        teilnahme = member in participating_members
        
        participation = Participation(
            member_id=member.id,
            event_id=event.id,
            teilnahme=teilnahme,
            responded_at=datetime.utcnow() - timedelta(days=random.randint(1, 7))
        )
        
        # BillBro-Daten nur für teilnehmende Members bei abgeschlossenen Events
        if teilnahme and generate_billbro and event.rechnungsbetrag_rappen:
            # Zufällige Esstyp-Verteilung
            esstyp_choices = [Esstyp.SPARSAM, Esstyp.NORMAL, Esstyp.ALLIN]
            esstyp_weights = [0.2, 0.6, 0.2]  # Meist NORMAL
            participation.esstyp = random.choices(esstyp_choices, weights=esstyp_weights)[0]
            
            # Realistische Schätzungen (rund um den echten Betrag)
            actual_amount_chf = event.rechnungsbetrag_rappen / 100
            # Schätzungen zwischen 70%-130% des echten Betrags
            guess_factor = random.uniform(0.7, 1.3)
            guess_chf = int(actual_amount_chf * guess_factor)
            participation.guess_bill_amount_rappen = guess_chf * 100
            
            # Differenz berechnen
            participation.diff_amount_rappen = abs(
                participation.guess_bill_amount_rappen - event.rechnungsbetrag_rappen
            )
            
            # Share berechnen basierend auf Esstyp
            if participation.esstyp == Esstyp.SPARSAM:
                participation.calculated_share_rappen = event.betrag_sparsam_rappen
            elif participation.esstyp == Esstyp.NORMAL:
                participation.calculated_share_rappen = event.betrag_normal_rappen
            elif participation.esstyp == Esstyp.ALLIN:
                participation.calculated_share_rappen = event.betrag_allin_rappen
        
        db.session.add(participation)
    
    # Nach dem Hinzufügen aller Participations: Points berechnen
    if generate_billbro and event.rechnungsbetrag_rappen:
        db.session.flush()  # Damit die IDs verfügbar sind
        GGLService.calculate_event_points(event.id)

def main():
    """Main seeding function"""
    print("🌱 Gourmen Test-Daten Seeder")
    print("=" * 40)
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        print("🗄️  Verbinde mit Datenbank...")
        
        # Erstelle Tabellen falls sie nicht existieren
        db.create_all()
        
        # Check ob bereits Daten vorhanden sind
        existing_members = Member.query.count()
        if existing_members > 0:
            print(f"⚠️  {existing_members} Mitglieder bereits vorhanden")
            response = input("Trotzdem fortfahren? (j/N): ")
            if response.lower() not in ['j', 'ja', 'y', 'yes']:
                print("❌ Abgebrochen")
                return
        
        try:
            # Testdaten erstellen
            members = create_test_members()
            events = create_test_events(members)
            
            print(f"\n✅ Seed erfolgreich abgeschlossen!")
            print(f"   👥 {len(members)} Mitglieder")
            print(f"   📅 {len(events)} Events")
            print(f"   🎯 BillBro-Daten für vergangene Events generiert")
            
            print(f"\n🚀 Login-Daten:")
            print(f"   Admin: max.mueller@gourmen.ch / Test123!")
            print(f"   User:  lisa.weber@gourmen.ch / Test123!")
            print(f"   (Alle Accounts haben Passwort: Test123!)")
            
        except Exception as e:
            print(f"❌ Fehler beim Seeding: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()

