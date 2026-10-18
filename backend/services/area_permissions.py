"""Explicit area permissions: no implicit admin/board escalation."""
from datetime import datetime
from flask_login import current_user
from backend.extensions import db
from backend.models.member_area_grant import MemberAreaGrant
from backend.services.action_confirmation import ActionConfirmationService


class AreaPermissionService:
    SCOPES = {'travel_documents': 'Reisedokumente lesen',
              'accounting_read': 'Buchhaltung lesen',
              'accounting_write': 'Buchhaltung bearbeiten (ohne Revisionsabschluss)'}
    FUNCTIONS = {'travel_documents': ('REISEKOMMISSAR',),
                 'accounting_read': ('SCHATZMEISTER', 'RECHNUNGSPRUEFER'),
                 'accounting_write': ('SCHATZMEISTER',)}

    @classmethod
    def has_scope(cls, member, scope):
        if scope not in cls.SCOPES or not member or not member.is_active:
            return False
        if member.is_admin() or any(member.has_funktion(f) for f in cls.FUNCTIONS.get(scope, ())):
            return True
        scopes = [scope, 'accounting_write'] if scope == 'accounting_read' else [scope]
        return MemberAreaGrant.query.filter(MemberAreaGrant.member_id == member.id,
            MemberAreaGrant.scope.in_(scopes), MemberAreaGrant.revoked_at.is_(None)).first() is not None

    @classmethod
    def replace_grants(cls, target, scopes, password):
        selected = set(scopes)
        if not selected.issubset(cls.SCOPES):
            raise ValueError('Unbekannte Bereichsfreigabe.')
        if not target.is_active and selected:
            raise ValueError('Freigaben sind nur fuer aktive Mitglieder moeglich.')
        if not ActionConfirmationService.check('area_permissions', target, password, admin=True):
            return False
        # check() refreshes/locks actor and target. Validate current active state again.
        if not target.is_active and selected:
            raise ValueError('Freigaben sind nur fuer aktive Mitglieder moeglich.')
        active = MemberAreaGrant.query.filter_by(member_id=target.id, revoked_at=None).all()
        now = datetime.utcnow()
        for grant in active:
            if grant.scope not in selected:
                grant.revoked_at, grant.revoked_by = now, current_user.id
        existing = {grant.scope for grant in active}
        for scope in selected - existing:
            db.session.add(MemberAreaGrant(member_id=target.id, scope=scope, granted_by=current_user.id, granted_at=now))
        target.rotate_auth_generation()
        # Caller commits history and identity rotation together, or rolls both back.
        return True
