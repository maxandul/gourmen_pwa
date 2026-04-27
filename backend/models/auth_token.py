from datetime import datetime
from enum import Enum

from backend.extensions import db


class AuthTokenPurpose(Enum):
    PASSWORD_RESET = "PASSWORD_RESET"
    MFA_RESET = "MFA_RESET"
    ONBOARDING = "ONBOARDING"
    MAGIC_LINK = "MAGIC_LINK"


class AuthToken(db.Model):
    __tablename__ = "auth_tokens"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(
        db.Integer,
        db.ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = db.Column(db.String(128), unique=True, nullable=False, index=True)
    purpose = db.Column(db.Enum(AuthTokenPurpose), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    request_ip = db.Column(db.String(45))

    __table_args__ = (
        db.Index("ix_auth_tokens_member_purpose_used_at", "member_id", "purpose", "used_at"),
    )

