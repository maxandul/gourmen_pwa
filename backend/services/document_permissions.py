"""Deny-by-default Drive item policies, independent of external sharing."""
from backend.extensions import db
from backend.models.document_policy import DocumentPolicy, DocumentPolicyChange
from backend.models.member import Member
from backend.models.event import Event
from backend.models.accounting import Receipt
from backend.services.area_permissions import AreaPermissionService


class DocumentPermissionService:
    ACCESS_LEVELS = {'club': 'Verein', 'board': 'Vorstand', 'finance': 'Finanzen'}
    MAINTENANCE_SCOPES = ('documents_manage', 'board_documents_manage',
                          'accounting_write', 'travel_manage', 'merch_manage')

    @staticmethod
    def policy(drive_id):
        return db.session.get(DocumentPolicy, drive_id) if drive_id else None

    @classmethod
    def can_read_item(cls, member, drive_id, *, is_folder):
        if not member or not member.is_active:
            return False
        policy = cls.policy(drive_id)
        if member.is_admin():
            return True
        if not policy or policy.is_folder != is_folder or policy.maintenance_scope not in cls.MAINTENANCE_SCOPES:
            return False
        if policy.access_level == 'club':
            return True
        if policy.access_level == 'board':
            return bool(member.vorstandsmitglied)
        if policy.access_level == 'finance':
            return AreaPermissionService.has_scope(member, 'accounting_read')
        return False

    @classmethod
    def can_manage_item(cls, member, drive_id, *, is_folder):
        if not cls.can_read_item(member, drive_id, is_folder=is_folder):
            return False
        if member.is_admin():
            return True
        return AreaPermissionService.has_scope(member, cls.policy(drive_id).maintenance_scope)

    @classmethod
    def can_read_folder(cls, member, drive_id, *, root_id=None):
        if drive_id and drive_id == root_id:
            return bool(member and member.is_active)
        return cls.can_read_item(member, drive_id, is_folder=True)

    @classmethod
    def can_read_document(cls, member, document, *, root_id=None):
        if not document or not cls.can_read_item(member, document.drive_file_id, is_folder=False):
            return False
        if not cls.can_read_folder(member, document.drive_parent_id, root_id=root_id):
            return False
        if document.event_id:
            event = db.session.get(Event, document.event_id)
            if not event or not event.is_visible_to(member):
                return False
        # A generic document alias must not bypass accounting receipt rights.
        from backend.services.accounting import AccountingService
        return all(AccountingService.can_read_receipt(receipt, member)
                   for receipt in Receipt.query.filter_by(drive_file_id=document.drive_file_id).all())

    @classmethod
    def can_manage_document(cls, member, document, *, root_id=None):
        return cls.can_read_document(member, document, root_id=root_id) and cls.can_manage_item(
            member, document.drive_file_id, is_folder=False)

    @classmethod
    def classify(cls, actor, drive_id, *, is_folder, access_level, maintenance_scope, reason, expected_before):
        """Stage policy + history atomically. Caller commits or rolls both back."""
        if not actor or not actor.id:
            raise PermissionError('Keine Berechtigung zur Zuordnung.')
        actor = Member.query.filter_by(id=actor.id).populate_existing().with_for_update().one()
        if not actor.is_active or not actor.is_admin():
            raise PermissionError('Keine Berechtigung zur Zuordnung.')
        reason = (reason or '').strip()
        if (not isinstance(drive_id, str) or not drive_id.strip() or len(drive_id) > 100
                or type(is_folder) is not bool or access_level not in cls.ACCESS_LEVELS
                or maintenance_scope not in cls.MAINTENANCE_SCOPES or not reason or len(reason) > 500):
            raise ValueError('Ungueltige Dokumentzuordnung.')
        policy = DocumentPolicy.query.filter_by(drive_id=drive_id).with_for_update().first()
        before = policy.snapshot() if policy else None
        if before != expected_before:
            raise ValueError('Zuordnung wurde zwischenzeitlich geaendert. Bitte neu laden.')
        if policy and policy.is_folder != is_folder:
            raise ValueError('Datei- und Ordnertyp duerfen nicht wechseln.')
        if not policy:
            policy = DocumentPolicy(drive_id=drive_id, is_folder=is_folder)
            db.session.add(policy)
        policy.access_level, policy.maintenance_scope = access_level, maintenance_scope
        db.session.add(DocumentPolicyChange(drive_id=drive_id, actor_id=actor.id,
                        reason=reason, before=before, after=policy.snapshot()))
        return policy
