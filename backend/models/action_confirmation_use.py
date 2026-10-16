"""Durable one-time consumption for creation intents without an existing target."""
from datetime import datetime

from backend.extensions import db


class ActionConfirmationUse(db.Model):
    __tablename__ = 'action_confirmation_uses'

    nonce_hash = db.Column(db.String(64), primary_key=True)
    used_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
