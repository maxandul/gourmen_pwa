"""Persisted report attempts with fixed content and an idempotent remote target."""
from datetime import datetime, timedelta

from backend.extensions import db
from backend.models.accounting_revision import AccountingRevision
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.accounting_pdf import AccountingPdfService
from backend.services.drive_storage import DriveStorageService


class AccountingReportService:
    @staticmethod
    def lock(revision_id):
        row = db.session.get(AccountingRevision, revision_id)
        if row is None:
            raise AccountingValidationError('Prüffassung nicht gefunden.')
        AccountingService.lock_fiscal_year(row.fiscal_year_id)
        return AccountingRevision.query.filter_by(id=revision_id).populate_existing().with_for_update().one()

    @classmethod
    def checkpoint(cls, revision_id, attempt, **values):
        row = cls.lock(revision_id)
        if row.report_attempt != attempt or row.report_state != 'working':
            raise AccountingValidationError('Berichtsversuch wurde ersetzt. Stand neu laden.')
        for key, value in values.items():
            setattr(row, key, value)
        db.session.commit()
        return row

    @classmethod
    def run(cls, revision_id, actor):
        attempt = None
        try:
            # Report retries never grant approval authority to finance delegates.
            if not actor or not actor.is_active or not (actor.is_admin() or actor.has_funktion('RECHNUNGSPRUEFER') or actor.has_funktion('SCHATZMEISTER')):
                raise AccountingValidationError('Berichtsaktion nicht erlaubt.')
            row = cls.lock(revision_id)
            if row.approved_at is None or row.snapshot is None:
                raise AccountingValidationError('Bericht benötigt eine gespeicherte Bestätigung.')
            if row.report_drive_id:
                db.session.rollback()
                return row.report_drive_id
            if row.report_state == 'working' and row.report_attempted_at and row.report_attempted_at > datetime.utcnow() - timedelta(minutes=5):
                raise AccountingValidationError('Bericht wird bearbeitet. Nach fünf Minuten erneut versuchen.')
            row.report_attempt += 1
            attempt = row.report_attempt
            row.report_attempted_at = datetime.utcnow()
            row.report_state = 'working'
            db.session.commit()  # Durable claim before any rendering or external I/O.

            if row.report_payload is None:
                payload = AccountingPdfService.generate_report(row.fiscal_year, approval=row)
                row = cls.checkpoint(revision_id, attempt, report_payload=payload)
            if row.report_reserved_id is None:
                reserved_id = DriveStorageService.reserve_file_id()
                row = cls.checkpoint(revision_id, attempt, report_reserved_id=reserved_id)
            if row.report_folder_id is None:
                folder_id = AccountingService.get_receipt_folder_id(row.fiscal_year.year)
                row = cls.checkpoint(revision_id, attempt, report_folder_id=folder_id)
            # Copy values, then release the transaction opened by expired ORM reads.
            payload, target, folder = row.report_payload, row.report_reserved_id, row.report_folder_id
            name = f'Revisorenbericht_{row.snapshot["year"]}_v{row.version}'
            db.session.rollback()
            DriveStorageService.upload_reserved_pdf(payload, target, folder, name)
            cls.checkpoint(revision_id, attempt, report_drive_id=target, report_state='complete')
            return target
        except Exception as exc:
            db.session.rollback()
            if attempt is not None:
                try:
                    row = cls.lock(revision_id)
                    if row.report_attempt == attempt and row.report_state == 'working':
                        row.report_state = 'failed'
                    db.session.commit()
                except Exception:
                    db.session.rollback()  # Working claim remains recoverable after timeout.
            if isinstance(exc, AccountingValidationError):
                raise
            raise AccountingValidationError('Bericht nicht bestätigt. In den Prüffassungen erneut versuchen; die Bestätigung bleibt erhalten.') from exc
