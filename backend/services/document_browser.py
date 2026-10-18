"""Permission-filtered presentation boundary over the Drive transport."""
from flask import current_app
from backend.services.document_permissions import DocumentPermissionService as Policy
from backend.services.drive_storage import DriveStorageService as Drive, DriveValidationError


class DocumentBrowserService:
    @staticmethod
    def require_folder(actor, folder_id, *, write=False):
        allowed = Policy.can_manage_item(actor, folder_id, is_folder=True) if write else Policy.can_read_folder(actor, folder_id, root_id=current_app.config.get('GOOGLE_DRIVE_ID'))
        if not allowed:
            raise PermissionError('Kein Zugriff auf diesen Ordner.')

    @staticmethod
    def require_document(actor, document, *, write=False):
        check = Policy.can_manage_document if write else Policy.can_read_document
        if not check(actor, document, root_id=current_app.config.get('GOOGLE_DRIVE_ID')):
            raise PermissionError('Kein Zugriff auf dieses Dokument.')

    @staticmethod
    def breadcrumbs(actor, crumbs):
        return [seg for seg in crumbs if Policy.can_read_folder(actor, seg.id, root_id=current_app.config.get('GOOGLE_DRIVE_ID'))]

    @classmethod
    def folders(cls, actor, folders):
        visible = [folder for folder in folders if Policy.can_read_folder(actor, folder.id, root_id=current_app.config.get('GOOGLE_DRIVE_ID'))]
        if not actor.is_admin():
            for folder in visible:
                if hasattr(folder, 'direct_child_count'):
                    folder.direct_child_count = None
        return visible

    @classmethod
    def listing(cls, actor, folder_id):
        cls.require_folder(actor, folder_id)
        listing = Drive.list_folder(folder_id)
        listing.subfolders = cls.folders(actor, listing.subfolders)
        listing.files = [row for row in listing.files if Policy.can_read_file_at(actor,
            row.drive_file_id, folder_id, root_id=current_app.config.get('GOOGLE_DRIVE_ID'))]
        for row in listing.files:
            row.can_manage = Policy.can_manage_item(actor, row.drive_file_id, is_folder=False)
        return listing

    @classmethod
    def search(cls, actor, query, scope_folder_id=None):
        if scope_folder_id:
            cls.require_folder(actor, scope_folder_id)
        hits = Drive.search_files(query, scope_folder_id=scope_folder_id)
        hits = [hit for hit in hits if Policy.can_read_file_at(actor,hit.drive_file_id,
            hit.parent_id,root_id=current_app.config.get('GOOGLE_DRIVE_ID'))]
        for hit in hits:
            hit.breadcrumb = cls.breadcrumbs(actor,hit.breadcrumb)
        return hits
