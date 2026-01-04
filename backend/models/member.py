from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db

class Role(Enum):
    MEMBER = 'MEMBER'
    ADMIN = 'ADMIN'

class Funktion(Enum):
    MEMBER = 'MEMBER'
    VEREINSPRAESIDENT = 'VEREINSPRAESIDENT'
    KOMMISSIONSPRAESIDENT = 'KOMMISSIONSPRAESIDENT'
    SCHATZMEISTER = 'SCHATZMEISTER'
    MARKETINGCHEF = 'MARKETINGCHEF'
    REISEKOMMISSAR = 'REISEKOMMISSAR'
    RECHNUNGSPRUEFER = 'RECHNUNGSPRUEFER'

# Nationalität choices for form validation
NATIONALITAET_CHOICES = [
    ('', 'Bitte wählen...'),
    ('CH', 'Schweiz'),
    ('IT', 'Italien'),
    ('Andere', 'Andere')
]

# Zimmerwunsch choices for form validation
ZIMMERWUNSCH_CHOICES = [
    ('', 'Bitte wählen...'),
    ('Einzelzimmer', 'Einzelzimmer'),
    ('Zweierzimmer', 'Zweierzimmer'),
    ('Egal', 'Egal')
]

class Member(db.Model, UserMixin):
    """Member model - contains non-sensitive data only"""
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Enum(Role), default=Role.MEMBER, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Personal data
    vorname = db.Column(db.String(100), nullable=False)
    nachname = db.Column(db.String(100), nullable=False)
    rufname = db.Column(db.String(100))
    geburtsdatum = db.Column(db.Date)
    nationalitaet = db.Column(db.String(50))
    
    # Contact data
    strasse = db.Column(db.String(200))
    hausnummer = db.Column(db.String(20))
    plz = db.Column(db.String(10))
    ort = db.Column(db.String(100))
    telefon = db.Column(db.String(50))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    passwort_hash = db.Column(db.String(255), nullable=False)
    
    # Association data
    funktion = db.Column(db.Enum(Funktion), default=Funktion.MEMBER)
    vorstandsmitglied = db.Column(db.Boolean, default=False)
    beitrittsjahr = db.Column(db.Integer)
    beitritt = db.Column(db.Date)  # Monatsbeginn (01.MM.YYYY)
    
    # Physical data
    koerpergroesse = db.Column(db.Integer)  # in cm
    schuhgroesse = db.Column(db.Float)      # EU size
    koerpergewicht = db.Column(db.Integer)  # in kg
    
    # Clothing data
    kleider_oberteil = db.Column(db.String(20))  # S, M, L, XL, etc.
    kleider_hosen = db.Column(db.String(20))
    kleider_cap = db.Column(db.String(20))
    
    # Preferences
    zimmerwunsch = db.Column(db.String(200))
    spirit_animal = db.Column(db.String(100))
    fuehrerschein = db.Column(db.String(200))  # Comma-separated list of categories
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    password_changed_at = db.Column(db.DateTime)
    
    # Relationships
    sensitive_data = db.relationship('MemberSensitive', backref='member', uselist=False, cascade='all, delete-orphan')
    mfa_data = db.relationship('MemberMFA', backref='member', uselist=False, cascade='all, delete-orphan')
    backup_codes = db.relationship('MFABackupCode', backref='member', cascade='all, delete-orphan')
    events_organized = db.relationship('Event', backref='organisator', foreign_keys='Event.organisator_id')
    participations = db.relationship('Participation', backref='member', cascade='all, delete-orphan')
    documents_uploaded = db.relationship('Document', backref='uploader', foreign_keys='Document.uploader_id')
    audit_events = db.relationship('AuditEvent', backref='actor', foreign_keys='AuditEvent.actor_id')
    
    def __repr__(self):
        return f'<Member {self.email}>'
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.vorname} {self.nachname}"
    
    @property
    def display_name(self):
        """Get display name (rufname or full name)"""
        return self.rufname or self.full_name
    
    @property
    def display_name_with_spirit(self):
        """Get display name with spirit animal prefix"""
        name = self.display_name
        if self.spirit_animal:
            return f"{self.spirit_animal} {name}"
        return name
    
    def set_password(self, password):
        """Set password hash"""
        self.passwort_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.passwort_hash, password)
    
    @property
    def needs_password_change(self):
        """Check if user needs to change password on first login"""
        return self.password_changed_at is None
    
    def is_admin(self):
        """Check if member is admin"""
        return self.role == Role.ADMIN
    
    def get_id(self):
        """Get user ID for Flask-Login"""
        return str(self.id)
    
    @property
    def nationalitaet_display(self):
        """Get display name for nationality"""
        if not self.nationalitaet:
            return None
        
        # Map values to display names
        display_names = {
            'CH': 'Schweiz',
            'IT': 'Italien',
            'Andere': 'Andere'
        }
        return display_names.get(self.nationalitaet, self.nationalitaet)
    
    @property
    def zimmerwunsch_display(self):
        """Get display name for zimmerwunsch"""
        if not self.zimmerwunsch:
            return None
        
        # Map values to display names
        display_names = {
            'Einzelzimmer': 'Einzelzimmer',
            'Zweierzimmer': 'Zweierzimmer',
            'Egal': 'Egal'
        }
        return display_names.get(self.zimmerwunsch, self.zimmerwunsch) 