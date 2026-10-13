"""Versioned login credentials and bounded MFA device trust."""
import hmac
import math
import time

from flask import current_app, request, session
from flask_login import login_user

from backend.extensions import db
from backend.services.security import SecurityService


class AuthenticationService:
    DEVICE_TRUST_SECONDS = 30 * 24 * 60 * 60

    @staticmethod
    def load_user(identifier):
        from backend.models.member import Member
        try:
            member_id, generation = identifier.split(':', 1)
            user = db.session.get(Member, int(member_id))
        except (AttributeError, TypeError, ValueError):
            user = None
        if (user and user.is_active and generation
                and hmac.compare_digest(user.auth_generation.encode(), generation.encode())):
            return user
        SecurityService.clear_auth_transients(current_app)
        for key in ('_user_id', '_fresh', '_id', 'remembered_device'):
            session.pop(key, None)
        session['_remember'] = 'clear'
        return None

    @staticmethod
    def complete_login(user, expected_generation, *, remember=False):
        # A commit may have expired/reloaded the row. Never bless an intervening reset.
        if not user.is_active or user.auth_generation != expected_generation:
            SecurityService.clear_auth_transients(current_app)
            return False
        return login_user(user, remember=remember)

    @classmethod
    def trusted_device(cls, user):
        grant = session.get('remembered_device')
        now = time.time()
        if isinstance(grant, dict):
            issued, expires = grant.get('issued_at'), grant.get('expires_at')
            try:
                valid_times = all(isinstance(value, (int, float)) and not isinstance(value, bool)
                                  and math.isfinite(value) for value in (issued, expires))
            except OverflowError:
                valid_times = False
            if (grant.get('user_id') == user.id
                    and grant.get('generation') == user.auth_generation
                    and valid_times and issued <= now < expires
                    and 0 < expires - issued <= cls.DEVICE_TRUST_SECONDS):
                return dict(grant)
        session.pop('remembered_device', None)
        return None

    @classmethod
    def issue_device_trust(cls, user):
        """Only call after a fresh, successful TOTP check."""
        now = int(time.time())
        session['remembered_device'] = {
            'user_id': user.id, 'generation': user.auth_generation,
            'issued_at': now, 'expires_at': now + cls.DEVICE_TRUST_SECONDS,
        }

    @staticmethod
    def retain_current(user, expected_generation, *, trust=None):
        """After commit only: carry this session into the new generation."""
        if not user.is_active or user.auth_generation != expected_generation:
            return False
        session['_user_id'] = user.get_id()
        SecurityService.revoke_step_up_access()
        session.pop('remembered_device', None)
        if trust:
            session['remembered_device'] = dict(trust, generation=user.auth_generation)
        cookie_name = current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
        if cookie_name in request.cookies or session.get('_remember') == 'set':
            session['_remember'] = 'set'
        return True
