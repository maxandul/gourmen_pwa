from datetime import datetime
from enum import Enum
from backend.extensions import db

class AuditAction(Enum):
    LOGIN = 'LOGIN'
    READ_SENSITIVE_SELF = 'READ_SENSITIVE_SELF'
    UPDATE_SENSITIVE_SELF = 'UPDATE_SENSITIVE_SELF'
    READ_SENSITIVE_OTHERS = 'READ_SENSITIVE_OTHERS'
    UPDATE_SENSITIVE_OTHERS = 'UPDATE_SENSITIVE_OTHERS'
    DELETE_DOC_SOFT = 'DELETE_DOC_SOFT'
    DELETE_DOC_HARD = 'DELETE_DOC_HARD'
    VIEW_MFA = 'VIEW_MFA'
    ENABLE_MFA = 'ENABLE_MFA'
    DISABLE_MFA = 'DISABLE_MFA'
    USE_BACKUP_CODE = 'USE_BACKUP_CODE'
    BILLBRO_COMPUTE = 'BILLBRO_COMPUTE'
    BILLBRO_ENTER_BILL = 'BILLBRO_ENTER_BILL'
    BILLBRO_RECORD_GUESS = 'BILLBRO_RECORD_GUESS'
    BILLBRO_MARK_ABSENT = 'BILLBRO_MARK_ABSENT'
    BILLBRO_MARK_PRESENT = 'BILLBRO_MARK_PRESENT'
    BILLBRO_SET_TOTAL = 'BILLBRO_SET_TOTAL'
    BILLBRO_START_SESSION = 'BILLBRO_START_SESSION'
    BILLBRO_SEND_REMINDER = 'BILLBRO_SEND_REMINDER'
    PUSH_SUBSCRIBE = 'PUSH_SUBSCRIBE'
    PUSH_UNSUBSCRIBE = 'PUSH_UNSUBSCRIBE'
    EVENT_ORGANIZER_CHANGED = 'EVENT_ORGANIZER_CHANGED'
    RSVP_UPDATE = 'RSVP_UPDATE'
    EVENT_EDIT = 'EVENT_EDIT'
    ADMIN_CREATE_EVENT = 'ADMIN_CREATE_EVENT'
    ADMIN_CREATE_MEMBER = 'ADMIN_CREATE_MEMBER'
    ADMIN_EDIT_MEMBER = 'ADMIN_EDIT_MEMBER'
    CHANGE_PASSWORD = 'CHANGE_PASSWORD'
    REQUEST_PASSWORD_RESET = 'REQUEST_PASSWORD_RESET'
    RESET_PASSWORD = 'RESET_PASSWORD'

class AuditEvent(db.Model):
    """Audit event model for security logging"""
    __tablename__ = 'audit_events'
    
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='SET NULL'), nullable=False)
    
    # Action details
    action = db.Column(db.Enum(AuditAction), nullable=False)
    entity = db.Column(db.String(50), nullable=False)  # member, member_sensitive, member_mfa, document, event, participation
    entity_id = db.Column(db.Integer)
    field = db.Column(db.String(100))  # Specific field if applicable
    
    # Metadata
    at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip = db.Column(db.String(45))  # IPv4 or IPv6
    extra_json = db.Column(db.JSON)  # Additional context data
    
    def __repr__(self):
        return f'<AuditEvent {self.action.value} by {self.actor_id} at {self.at}>'
    
    @property
    def actor(self):
        """Get actor"""
        from backend.models.member import Member
        return Member.query.get(self.actor_id)
    
    @property
    def display_action(self):
        """Get human-readable action name"""
        action_names = {
            AuditAction.LOGIN: 'Login',
            AuditAction.READ_SENSITIVE_SELF: 'Sensible Daten gelesen (eigene)',
            AuditAction.UPDATE_SENSITIVE_SELF: 'Sensible Daten bearbeitet (eigene)',
            AuditAction.READ_SENSITIVE_OTHERS: 'Sensible Daten gelesen (andere)',
            AuditAction.UPDATE_SENSITIVE_OTHERS: 'Sensible Daten bearbeitet (andere)',
            AuditAction.DELETE_DOC_SOFT: 'Dokument gelöscht (Soft)',
            AuditAction.DELETE_DOC_HARD: 'Dokument gelöscht (Hard)',
            AuditAction.VIEW_MFA: '2FA angesehen',
            AuditAction.ENABLE_MFA: '2FA aktiviert',
            AuditAction.DISABLE_MFA: '2FA deaktiviert',
            AuditAction.USE_BACKUP_CODE: 'Backup-Code verwendet',
            AuditAction.BILLBRO_COMPUTE: 'BillBro berechnet',
            AuditAction.BILLBRO_ENTER_BILL: 'BillBro Rechnungsbetrag eingegeben',
            AuditAction.BILLBRO_RECORD_GUESS: 'BillBro Schätzung eingegeben',
            AuditAction.BILLBRO_MARK_ABSENT: 'BillBro Teilnehmer abgemeldet',
            AuditAction.BILLBRO_MARK_PRESENT: 'BillBro Teilnehmer angemeldet',
            AuditAction.BILLBRO_SET_TOTAL: 'BillBro Gesamtbetrag festgelegt',
            AuditAction.BILLBRO_START_SESSION: 'BillBro Session gestartet',
            AuditAction.BILLBRO_SEND_REMINDER: 'BillBro Erinnerung gesendet',
                    AuditAction.PUSH_SUBSCRIBE: 'Push-Notifications aktiviert',
        AuditAction.PUSH_UNSUBSCRIBE: 'Push-Notifications deaktiviert',
        AuditAction.EVENT_ORGANIZER_CHANGED: 'Event Organisator geändert',
            AuditAction.RSVP_UPDATE: 'Teilnahme aktualisiert',
            AuditAction.EVENT_EDIT: 'Event bearbeitet',
            AuditAction.ADMIN_CREATE_EVENT: 'Event erstellt (Admin)',
            AuditAction.ADMIN_CREATE_MEMBER: 'Mitglied erstellt (Admin)',
            AuditAction.ADMIN_EDIT_MEMBER: 'Mitglied bearbeitet (Admin)',
            AuditAction.CHANGE_PASSWORD: 'Passwort geändert',
            AuditAction.REQUEST_PASSWORD_RESET: 'Passwort-Reset angefordert',
            AuditAction.RESET_PASSWORD: 'Passwort zurückgesetzt'
        }
        return action_names.get(self.action, self.action.value)
    
    @property
    def display_entity(self):
        """Get human-readable entity name"""
        entity_names = {
            'member': 'Mitglied',
            'member_sensitive': 'Sensible Daten',
            'member_mfa': '2FA',
            'document': 'Dokument',
            'event': 'Event',
            'participation': 'Teilnahme'
        }
        return entity_names.get(self.entity, self.entity) 