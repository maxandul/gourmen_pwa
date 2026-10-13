"""Restrict authenticated initial-password accounts until their first change."""
from flask import flash, jsonify, redirect, request, session, url_for
from flask_login import current_user

from backend.services.security import SecurityService


class PasswordChangeService:
    # Public/token-authenticated flows retain their own access checks.
    ALLOWED_ENDPOINTS = frozenset({
        'static', 'service_worker', 'health',
        'auth.change_password', 'auth.logout', 'auth.reset_password',
        'auth.activate', 'auth.reset_2fa',
    })
    PUBLIC_BLUEPRINTS = frozenset({'public', 'cron', 'calendar_feed'})

    @staticmethod
    def _target(value):
        target = SecurityService.local_return_target(value)
        # Authentication intermediates are not useful destinations after completion.
        if target and not target.split('?', 1)[0].split('#', 1)[0].startswith('/auth/'):
            return target
        return None

    @classmethod
    def remember_target(cls, member_id, value):
        """Keep the first valid target, bound to this account."""
        stored = session.get('password_change_return')
        if (isinstance(stored, dict) and stored.get('member_id') == member_id
                and cls._target(stored.get('target'))):
            return
        session.pop('password_change_return', None)
        target = cls._target(value)
        if target:
            session['password_change_return'] = {'member_id': member_id, 'target': target}

    @classmethod
    def after_login_target(cls, member, target):
        """Called only after password and any required MFA have succeeded."""
        if member.needs_password_change:
            cls.remember_target(member.id, target)
            flash('Bitte ändere dein Passwort bei der ersten Anmeldung.', 'info')
            return url_for('auth.change_password')
        return SecurityService.local_return_target(target) or url_for('dashboard.index')

    @classmethod
    def consume_target(cls, member_id):
        stored = session.pop('password_change_return', None)
        if isinstance(stored, dict) and stored.get('member_id') == member_id:
            return cls._target(stored.get('target'))
        return None

    @classmethod
    def enforce(cls):
        """Global request boundary; no protected view runs before completion."""
        if (request.endpoint is None or request.endpoint in cls.ALLOWED_ENDPOINTS
                or request.blueprint in cls.PUBLIC_BLUEPRINTS):
            return None
        if not current_user.is_authenticated or not current_user.needs_password_change:
            return None
        json_request = (request.is_json or request.path.startswith('/api/')
                        or request.accept_mimetypes.best == 'application/json')
        # Preserve navigation only. Never replay a rejected POST or API mutation.
        if request.method in ('GET', 'HEAD') and not json_request:
            cls.remember_target(current_user.id, request.full_path if request.query_string else request.path)
        location = url_for('auth.change_password')
        if json_request:
            response = jsonify(error='password_change_required',
                               message='Bitte ändere zuerst dein Passwort.', next=location)
            response.status_code = 403
        else:
            response = redirect(location, code=303 if request.method not in ('GET', 'HEAD') else 302)
        response.headers['Cache-Control'] = 'no-store'
        return response
