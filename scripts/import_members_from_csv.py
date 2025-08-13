#!/usr/bin/env python3
"""
Gourmen Member CSV Import Script
Importiert echte Mitgliederdaten aus einem CSV/Google Sheets Export
"""

import os
import sys
import csv
import pandas as pd
from datetime import datetime, date
from dateutil import parser

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Role

def parse_date(date_string):
    """Parse various date formats to date object"""
    if not date_string or pd.isna(date_string):
        return None
    
    try:
        # Handle German date format and various others
        if isinstance(date_string, str):
            # Common German formats
            for fmt in ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    return datetime.strptime(date_string.strip(), fmt).date()
                except ValueError:
                    continue
            # Try dateutil parser as fallback
            return parser.parse(date_string, dayfirst=True).date()
        elif isinstance(date_string, datetime):
            return date_string.date()
        elif isinstance(date_string, date):
            return date_string
    except:
        print(f"⚠️  Konnte Datum nicht parsen: {date_string}")
        return None

def clean_string(value, max_length=None):
    """Clean and validate string values"""
    if pd.isna(value) or value is None:
        return None
    
    cleaned = str(value).strip()
    if not cleaned:
        return None
    
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
        
    return cleaned

def parse_number(value):
    """Parse number values safely"""
    if pd.isna(value) or value is None or value == '':
        return None
    try:
        if isinstance(value, str):
            # Remove common non-numeric characters
            cleaned = value.replace(',', '.').strip()
            return float(cleaned) if '.' in cleaned else int(cleaned)
        return value
    except:
        return None

def import_members_from_csv(csv_file_path, encoding='utf-8'):
    """Import members from CSV file"""
    print(f"📁 Importiere Mitglieder aus: {csv_file_path}")
    
    try:
        # Try reading with pandas for better CSV handling
        df = pd.read_csv(csv_file_path, encoding=encoding)
    except UnicodeDecodeError:
        print("⚠️  UTF-8 Encoding fehlgeschlagen, versuche Windows-1252...")
        try:
            df = pd.read_csv(csv_file_path, encoding='windows-1252')
        except UnicodeDecodeError:
            print("⚠️  Windows-1252 fehlgeschlagen, versuche latin1...")
            df = pd.read_csv(csv_file_path, encoding='latin1')
    
    print(f"📊 CSV gelesen: {len(df)} Zeilen, {len(df.columns)} Spalten")
    print(f"📋 Spalten: {list(df.columns)}")
    
    # Ask user to map columns if they don't match expected names
    column_mapping = map_columns(df.columns)
    
    imported_count = 0
    updated_count = 0
    errors = []
    
    for index, row in df.iterrows():
        try:
            # Extract data using mapping
            email = clean_string(row.get(column_mapping.get('email')))
            if not email:
                errors.append(f"Zeile {index + 2}: Keine Email-Adresse")
                continue
                
            vorname = clean_string(row.get(column_mapping.get('vorname')), 100)
            nachname = clean_string(row.get(column_mapping.get('nachname')), 100)
            
            if not vorname or not nachname:
                errors.append(f"Zeile {index + 2}: Vor- oder Nachname fehlt")
                continue
            
            # Check if member already exists
            existing_member = Member.query.filter_by(email=email).first()
            
            if existing_member:
                print(f"  🔄 Aktualisiere: {vorname} {nachname} ({email})")
                member = existing_member
                updated_count += 1
            else:
                print(f"  ✅ Neu: {vorname} {nachname} ({email})")
                member = Member(email=email)
                # Set default password for new members
                member.set_password("Gourmen2025!")  # They should change this
                imported_count += 1
            
            # Update all fields
            member.vorname = vorname
            member.nachname = nachname
            member.rufname = clean_string(row.get(column_mapping.get('rufname')), 100)
            member.geburtsdatum = parse_date(row.get(column_mapping.get('geburtsdatum')))
            member.nationalitaet = clean_string(row.get(column_mapping.get('nationalitaet')), 50)
            
            # Address
            member.strasse = clean_string(row.get(column_mapping.get('strasse')), 200)
            member.hausnummer = clean_string(row.get(column_mapping.get('hausnummer')), 20)
            member.plz = clean_string(row.get(column_mapping.get('plz')), 10)
            member.ort = clean_string(row.get(column_mapping.get('ort')), 100)
            member.telefon = clean_string(row.get(column_mapping.get('telefon')), 50)
            
            # Association data
            member.funktion = clean_string(row.get(column_mapping.get('funktion')), 100)
            member.beitrittsjahr = parse_number(row.get(column_mapping.get('beitrittsjahr')))
            
            # Physical data
            member.koerpergroesse = parse_number(row.get(column_mapping.get('koerpergroesse')))
            member.schuhgroesse = parse_number(row.get(column_mapping.get('schuhgroesse')))
            member.koerpergewicht = parse_number(row.get(column_mapping.get('koerpergewicht')))
            
            # Clothing
            member.kleider_oberteil = clean_string(row.get(column_mapping.get('kleider_oberteil')), 20)
            member.kleider_hosen = clean_string(row.get(column_mapping.get('kleider_hosen')), 20)
            member.kleider_cap = clean_string(row.get(column_mapping.get('kleider_cap')), 20)
            
            # Preferences
            member.zimmerwunsch = clean_string(row.get(column_mapping.get('zimmerwunsch')), 200)
            member.spirit_animal = clean_string(row.get(column_mapping.get('spirit_animal')), 100)
            
            # Set role and status
            member.role = Role.MEMBER  # Default, admin can be changed manually
            member.is_active = True
            member.updated_at = datetime.utcnow()
            
            if not existing_member:
                db.session.add(member)
                
        except Exception as e:
            errors.append(f"Zeile {index + 2}: {str(e)}")
            continue
    
    # Commit changes
    try:
        db.session.commit()
        print(f"\n✅ Import erfolgreich abgeschlossen!")
        print(f"   ➕ {imported_count} neue Mitglieder")
        print(f"   🔄 {updated_count} aktualisierte Mitglieder")
        
        if errors:
            print(f"\n⚠️  {len(errors)} Fehler aufgetreten:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"   {error}")
            if len(errors) > 10:
                print(f"   ... und {len(errors) - 10} weitere")
                
        print(f"\n🔑 Standard-Passwort für neue Mitglieder: Gourmen2025!")
        print(f"   (Mitglieder sollten ihr Passwort beim ersten Login ändern)")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Fehler beim Speichern: {e}")
        raise

def map_columns(csv_columns):
    """Map CSV columns to member fields"""
    print(f"\n📋 Spalten-Mapping:")
    print(f"Verfügbare CSV-Spalten: {list(csv_columns)}")
    
    # Common German field mappings
    auto_mapping = {
        'email': ['email', 'e-mail', 'mail', 'e_mail'],
        'vorname': ['vorname', 'vornamen', 'first_name', 'firstname'],
        'nachname': ['nachname', 'nachnamen', 'last_name', 'lastname', 'familienname'],
        'rufname': ['rufname', 'spitzname', 'nickname'],
        'geburtsdatum': ['geburtsdatum', 'geburtstag', 'birthday', 'birth_date', 'geb_datum'],
        'nationalitaet': ['nationalitaet', 'nationalität', 'nationality'],
        'strasse': ['strasse', 'straße', 'street', 'adresse'],
        'hausnummer': ['hausnummer', 'nr', 'number', 'haus_nr'],
        'plz': ['plz', 'postleitzahl', 'postal_code', 'zip'],
        'ort': ['ort', 'stadt', 'city', 'place'],
        'telefon': ['telefon', 'phone', 'tel', 'handy', 'mobile'],
        'funktion': ['funktion', 'position', 'rolle'],
        'beitrittsjahr': ['beitrittsjahr', 'eintrittsjahr', 'join_year'],
        'koerpergroesse': ['koerpergroesse', 'körpergröße', 'groesse', 'größe', 'height'],
        'schuhgroesse': ['schuhgroesse', 'schuhgröße', 'shoe_size'],
        'koerpergewicht': ['koerpergewicht', 'körpergewicht', 'gewicht', 'weight'],
        'kleider_oberteil': ['kleider_oberteil', 'oberteil', 'shirt_size', 't_shirt'],
        'kleider_hosen': ['kleider_hosen', 'hosen', 'pants_size'],
        'kleider_cap': ['kleider_cap', 'cap', 'mütze', 'hat_size'],
        'zimmerwunsch': ['zimmerwunsch', 'zimmer', 'room_preference'],
        'spirit_animal': ['spirit_animal', 'tier', 'krafttier', 'lieblingstier']
    }
    
    mapping = {}
    csv_columns_lower = [col.lower().replace(' ', '_').replace('-', '_') for col in csv_columns]
    
    # Auto-map columns
    for field, possible_names in auto_mapping.items():
        for csv_col, csv_col_lower in zip(csv_columns, csv_columns_lower):
            if any(name.lower() in csv_col_lower for name in possible_names):
                mapping[field] = csv_col
                print(f"  ✅ {field} → {csv_col}")
                break
    
    # Check for required fields
    required_fields = ['email', 'vorname', 'nachname']
    missing_required = [field for field in required_fields if field not in mapping]
    
    if missing_required:
        print(f"\n⚠️  Erforderliche Felder fehlen: {missing_required}")
        print("Bitte manuell zuordnen:")
        for field in missing_required:
            while True:
                print(f"Verfügbare Spalten: {list(csv_columns)}")
                user_input = input(f"Spalte für '{field}': ").strip()
                if user_input in csv_columns:
                    mapping[field] = user_input
                    break
                else:
                    print("❌ Ungültige Spalte. Bitte erneut versuchen.")
    
    return mapping

def main():
    """Main import function"""
    print("📥 Gourmen Mitglieder CSV Import")
    print("=" * 40)
    
    # Get CSV file path from user
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = input("Pfad zur CSV-Datei: ").strip()
    
    if not os.path.exists(csv_file):
        print(f"❌ Datei nicht gefunden: {csv_file}")
        return
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        print("🗄️  Verbinde mit Datenbank...")
        
        # Import members
        try:
            import_members_from_csv(csv_file)
            
            # Show summary
            total_members = Member.query.count()
            print(f"\n📊 Gesamtanzahl Mitglieder in der Datenbank: {total_members}")
            
        except Exception as e:
            print(f"❌ Import fehlgeschlagen: {e}")
            raise

if __name__ == "__main__":
    main()
