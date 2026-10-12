"""Address-bound Google verification using the existing 128-character hash column."""
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from backend.extensions import db
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.models.member import Member


@dataclass(frozen=True)
class GoogleAddressSnapshot:
    id: int
    google_email: str
    display_name: str
    google_email_verified: bool
    token: str | None = None


def _lookup_hash(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _bound_hash(token, email):
    # The random token supplies entropy; no plaintext address in the link or DB token.
    binding = hashlib.sha256((token + '\0' + email).encode('utf-8')).hexdigest()
    return _lookup_hash(token) + binding


def _locked_member(member_id):
    return Member.query.filter_by(id=member_id).populate_existing().with_for_update().first()


class GoogleEmailVerificationService:
    @staticmethod
    def issue(member_id, *, email=None, request_ip=None):
        """Serialize replacement with address changes; commit before external mail."""
        member = _locked_member(member_id)
        if not member or not member.is_active:
            db.session.rollback()
            return None, 'missing'
        if email is not None:
            if (member.google_email or '').lower() != email:
                member.google_email_verified = False
                member.google_email_verified_at = None
            member.google_email = email
        if not member.google_email:
            db.session.rollback()
            return None, 'missing'
        if member.google_email_verified:
            db.session.commit()
            return None, 'verified'
        now = datetime.utcnow()
        AuthToken.query.filter_by(member_id=member.id,
                                  purpose=AuthTokenPurpose.GOOGLE_EMAIL_VERIFY,
                                  used_at=None).update({'used_at': now}, synchronize_session=False)
        token = secrets.token_urlsafe(32)
        db.session.add(AuthToken(member_id=member.id,
                                 purpose=AuthTokenPurpose.GOOGLE_EMAIL_VERIFY,
                                 token_hash=_bound_hash(token, member.google_email),
                                 expires_at=now + timedelta(days=7), request_ip=request_ip))
        delivery = GoogleAddressSnapshot(member.id, member.google_email,
                                        member.display_name, False, token)
        db.session.commit()
        return delivery, None

    @staticmethod
    def consume(token):
        """Recheck after the member lock and consume once before returning an invite target."""
        if len(token) != 43:
            return None, 'missing'
        candidate = AuthToken.query.filter(
            AuthToken.purpose == AuthTokenPurpose.GOOGLE_EMAIL_VERIFY,
            AuthToken.token_hash.startswith(_lookup_hash(token)),
        ).first()
        if candidate is None:
            return None, 'missing'
        member = _locked_member(candidate.member_id)
        row = AuthToken.query.filter_by(id=candidate.id).populate_existing().first()
        error = None
        if (not member or not member.is_active or not member.google_email or not row
                or row.purpose != AuthTokenPurpose.GOOGLE_EMAIL_VERIFY
                or not hmac.compare_digest(row.token_hash, _bound_hash(token, member.google_email))):
            error = 'missing'
        elif row.used_at is not None:
            error = 'used'
        elif row.expires_at <= datetime.utcnow():
            error = 'expired'
        if error:
            db.session.rollback()
            return None, error
        now = datetime.utcnow()
        consumed = AuthToken.query.filter_by(id=row.id, used_at=None).filter(
            AuthToken.expires_at > now,
        ).update({'used_at': now}, synchronize_session=False)
        if consumed != 1:
            db.session.rollback()
            return None, 'used'
        member.google_email_verified = True
        member.google_email_verified_at = now
        verified = GoogleAddressSnapshot(member.id, member.google_email, member.display_name, True)
        db.session.commit()
        return verified, None
