from datetime import datetime
from enum import Enum
from backend.extensions import db

class DocumentCategory(Enum):
    VEREIN = 'VEREIN'
    EVENT = 'EVENT'
    FOTO = 'FOTO'
    STATUTEN = 'STATUTEN'
    SONST = 'SONST'

class DocumentVisibility(Enum):
    PUBLIC = 'PUBLIC'
    MEMBER = 'MEMBER'
    ADMIN = 'ADMIN'

class Document(db.Model):
    """Document model for links and documents"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    
    # Classification
    category = db.Column(db.Enum(DocumentCategory), nullable=False)
    visibility = db.Column(db.Enum(DocumentVisibility), default=DocumentVisibility.MEMBER, nullable=False)
    
    # Relationships
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='SET NULL'))
    uploader_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='SET NULL'), nullable=False)
    
    # Metadata
    checksum = db.Column(db.String(64))  # For future file uploads
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.id}: {self.title}>'
    
    @property
    def event(self):
        """Get associated event"""
        from backend.models.event import Event
        return Event.query.get(self.event_id) if self.event_id else None
    
    @property
    def uploader(self):
        """Get uploader"""
        from backend.models.member import Member
        return Member.query.get(self.uploader_id)
    
    @property
    def is_deleted(self):
        """Check if document is soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def display_category(self):
        """Get human-readable category name"""
        category_names = {
            DocumentCategory.VEREIN: 'Verein',
            DocumentCategory.EVENT: 'Event',
            DocumentCategory.FOTO: 'Foto',
            DocumentCategory.STATUTEN: 'Statuten',
            DocumentCategory.SONST: 'Sonst'
        }
        return category_names.get(self.category, self.category.value)
    
    @property
    def display_visibility(self):
        """Get human-readable visibility name"""
        visibility_names = {
            DocumentVisibility.PUBLIC: 'Öffentlich',
            DocumentVisibility.MEMBER: 'Mitglieder',
            DocumentVisibility.ADMIN: 'Admin'
        }
        return visibility_names.get(self.visibility, self.visibility.value) 