"""Local access classification; Drive remains authoritative for file contents."""
from datetime import datetime
from backend.extensions import db


class DocumentPolicy(db.Model):
    __tablename__ = 'document_policies'
    drive_id = db.Column(db.String(100), primary_key=True)
    is_folder = db.Column(db.Boolean, nullable=False)
    access_level = db.Column(db.String(32), nullable=False)
    maintenance_scope = db.Column(db.String(64), nullable=False)

    def snapshot(self):
        return {key: getattr(self, key) for key in ('is_folder', 'access_level', 'maintenance_scope')}


class DocumentPolicyChange(db.Model):
    __tablename__ = 'document_policy_changes'
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.String(100), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    before = db.Column(db.JSON)
    after = db.Column(db.JSON, nullable=False)
