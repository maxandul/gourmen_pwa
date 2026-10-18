"""Canonical primary email lookup; no account merge or provider alias rules."""
from backend.extensions import db
from backend.models.member import Member
from backend.services.security import SecurityService


class PrimaryEmailService:
    normalize = staticmethod(SecurityService.normalized_primary_email)

    @staticmethod
    def query(value):
        return Member.query.filter(db.func.lower(db.func.trim(Member.email, ' \t\r\n\v\f')) == PrimaryEmailService.normalize(value))

    @classmethod
    def find_active(cls, value):
        matches = cls.query(value).limit(2).all()
        return matches[0] if len(matches) == 1 and matches[0].is_active else None
