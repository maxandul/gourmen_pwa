"""Inline reauthentication with transactional one-time consumption."""
import hashlib
import re
import secrets

from flask import abort, current_app, flash, request, session
from flask_login import current_user
from itsdangerous import BadData, URLSafeTimedSerializer

from backend.models.member import Member, Role
from backend.models.action_confirmation_use import ActionConfirmationUse
from backend.extensions import db
from backend.services.security import SecurityService


class ActionConfirmationService:
    MAX_AGE = 600
    ACTIONS = {'password_change', 'mfa_enroll', 'mfa_disable',
               'admin_password', 'admin_mfa', 'permissions', 'member_create'}

    @staticmethod
    def serializer():
        return URLSafeTimedSerializer(current_app.secret_key, salt='action-confirmation-v1')

    @classmethod
    def issue(cls, action, target=None):
        if action not in cls.ACTIONS:
            raise ValueError('Invalid action confirmation context')
        if not current_user.is_authenticated:
            abort(403)
        if 'action_session' not in session:
            session['action_session'] = secrets.token_urlsafe(32)
        payload = {
            'action': action, 'actor': current_user.get_id(),
            'session': session['action_session'], 'target': target.id if target else None,
            'generation': target.auth_generation if target else None,
        }
        if action == 'member_create':
            payload['nonce'] = secrets.token_urlsafe(32)
        return cls.serializer().dumps(payload)

    @classmethod
    def check(cls, action, target, password, *, admin=False):
        # Resolve the app-owned limiter at request time (blueprints may be
        # imported before the app factory and multiple apps exist in tests).
        limiter = current_app.extensions['gourmen_limiter']
        with limiter.limit('5 per minute', scope='action-confirmation', override_defaults=False):
            return cls._check(action, target, password, admin=admin)

    @classmethod
    def _check(cls, action, target, password, *, admin=False):
        """Hold locks until mutation and its consumption are committed together.

        No reusable grant is issued. A rolled-back mutation may be retried with
        a fresh password proof. Existing targets consume through generation
        rotation; member creation consumes its nonce through a unique receipt.
        """
        actor_id = current_user.id
        login_identity = session.get('_user_id')
        if admin:
            # Match _validate_admin_continuity to avoid inverse lock ordering.
            Member.query.filter_by(role=Role.ADMIN).order_by(Member.id).with_for_update().all()
        actor = SecurityService.lock_credential_member(actor_id)
        creating = action == 'member_create' and admin and target is None
        target = SecurityService.lock_credential_member(target.id) if target else None
        valid_actor = (actor and actor.is_active and actor.get_id() == login_identity
                       and (not admin or actor.is_admin()))
        if not valid_actor:
            # Never render a fresh privileged form after losing the actor's
            # session or permissions while waiting for the lock.
            abort(403)
        try:
            payload = cls.serializer().loads(request.form.get('action_token', ''), max_age=cls.MAX_AGE)
        except BadData:
            payload = None
        expected = {
            'action': action, 'actor': login_identity,
            'session': session.get('action_session'), 'target': target.id if target else None,
            'generation': target.auth_generation if target else None,
        }
        nonce = payload.get('nonce') if isinstance(payload, dict) else None
        if creating and isinstance(nonce, str) and re.fullmatch(r'[A-Za-z0-9_-]{43}', nonce):
            expected['nonce'] = nonce
        if (action not in cls.ACTIONS or (not target and not creating)
                or (action == 'member_create' and not creating)
                or (creating and 'nonce' not in expected)
                or not session.get('action_session') or payload != expected
                or (not admin and actor.id != target.id)):
            flash('Die Aktionsbestätigung ist abgelaufen oder der Kontostand hat sich geändert. '
                  'Bitte prüfe das Formular und bestätige die Aktion erneut.', 'error')
            return False
        if not password or not actor.check_password(password):
            flash('Bitte bestätige diese Aktion mit deinem aktuellen Passwort.', 'error')
            return False
        if creating:
            nonce_hash = hashlib.sha256(nonce.encode('ascii')).hexdigest()
            if db.session.get(ActionConfirmationUse, nonce_hash):
                flash('Dieser Anlageauftrag wurde bereits verwendet. '
                      'Bitte öffne für ein weiteres Mitglied ein neues Formular.', 'error')
                return False
            # No commit here: the unique receipt and new member must succeed
            # together. Actor locks serialize requests; the PK also guards races.
            db.session.add(ActionConfirmationUse(nonce_hash=nonce_hash))
        return True
