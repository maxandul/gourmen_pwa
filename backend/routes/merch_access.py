"""Merch v2: Feature-Flag-Check und rollenbasierte Decorators.

Specs: docs/capabilities/merch.md Abschnitt 11.4.
"""

from __future__ import annotations

from functools import wraps

from flask import abort, current_app
from flask_login import current_user

from backend.models.member import Funktion


def require_merch_v2_enabled() -> None:
    if not current_app.config.get('MERCH_V2_ENABLED'):
        abort(404)


def marketing_chief_or_admin_required(f):
    """Cockpit und Sortiments-Routen: Marketingchef oder Admin."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_active', False):
            abort(403)
        if current_user.is_admin():
            return f(*args, **kwargs)
        if getattr(current_user, 'funktion', None) == Funktion.MARKETINGCHEF:
            return f(*args, **kwargs)
        abort(403)

    return decorated_function


def merch_statistics_view_required(f):
    """Vereins- und KPI-Statistik: Marketingchef, Schatzmeister oder Admin (Lesen).

    Spec: docs/capabilities/merch.md Sektion 14.3 Datenzugriff fuer Jahresreport.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_active', False):
            abort(403)
        if current_user.is_admin():
            return f(*args, **kwargs)
        fx = getattr(current_user, 'funktion', None)
        if fx in (Funktion.MARKETINGCHEF, Funktion.SCHATZMEISTER):
            return f(*args, **kwargs)
        abort(403)

    return decorated_function


def treasury_marketing_or_admin_required(f):
    """Zusaetzlich fuer paid-Markierungen: Schatzmeister, Marketingchef oder Admin."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_active', False):
            abort(403)
        if current_user.is_admin():
            return f(*args, **kwargs)
        fx = getattr(current_user, 'funktion', None)
        if fx in (Funktion.MARKETINGCHEF, Funktion.SCHATZMEISTER):
            return f(*args, **kwargs)
        abort(403)

    return decorated_function


def merch_legacy_receivables_required(f):
    """Read-only Legacy-Forderungen: Marketingchef, Schatzmeister oder Admin."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_active', False):
            abort(403)
        if current_user.is_admin():
            return f(*args, **kwargs)
        fx = getattr(current_user, 'funktion', None)
        if fx in (Funktion.MARKETINGCHEF, Funktion.SCHATZMEISTER):
            return f(*args, **kwargs)
        abort(403)

    return decorated_function
