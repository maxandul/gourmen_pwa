"""Versionsgebundene Revision; alle lokalen Zustandswechsel sind atomar."""
from datetime import datetime
from functools import wraps
from types import SimpleNamespace

from backend.extensions import db
from backend.models.accounting import Account, AccountKind, Booking, BudgetEntry, FiscalYearStatus, Receipt, RevisionComment
from backend.models.accounting_revision import AccountingRevision
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.area_permissions import AreaPermissionService


def atomic(method):
    @wraps(method)
    def wrapped(*args, **kwargs):
        try:
            result = method(*args, **kwargs)
            db.session.commit()
            return result
        except AccountingValidationError:
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            raise AccountingValidationError('Revisionsänderung nicht bestätigt. Stand neu laden.') from exc
    return wrapped


class AccountingRevisionService:
    @staticmethod
    def require_actor(actor, action):
        native = 'RECHNUNGSPRUEFER' if action == 'approve' else 'SCHATZMEISTER'
        allowed = actor and actor.is_active and (actor.is_admin() or actor.has_funktion(native))
        if action == 'comment':
            allowed = actor and actor.is_active and (
                AreaPermissionService.has_scope(actor, 'accounting_write') or actor.has_funktion('RECHNUNGSPRUEFER'))
        if not allowed:
            raise AccountingValidationError('Revisionsaktion nicht erlaubt.')

    @staticmethod
    def lock(year_id, expected_version):
        fy = AccountingService.lock_fiscal_year(year_id)
        if type(expected_version) is not int or expected_version != fy.review_version:
            raise AccountingValidationError('Prüffassung wurde geändert. Stand neu laden.')
        return fy

    @staticmethod
    def current(fy):
        return AccountingRevision.query.filter_by(fiscal_year_id=fy.id, version=fy.review_version).first()

    @classmethod
    def active_snapshot(cls, fy):
        revision = cls.current(fy) if not fy.is_open else None
        return revision.snapshot if revision else None

    @staticmethod
    def summary(snapshot):
        rows = snapshot['bookings']
        income = sum(b['amount_rappen'] for b in rows if b['direction'] == 'in')
        expense = sum(b['amount_rappen'] for b in rows if b['direction'] == 'out')
        expense_ids = {a['id'] for a in snapshot['accounts'] if a['kind'] == 'expense'}
        budget = sum(b['amount_rappen'] for b in snapshot['budget'] if b['account_id'] in expense_ids)
        return dict(income_rappen=income, expense_rappen=expense, result_rappen=income-expense,
                    open_receipts=snapshot.get('open_receipts', 0), booking_count=len(rows),
                    budget_total_rappen=budget, budget_used_pct=round(expense/budget*100) if budget else None)

    @staticmethod
    def budget_rows(snapshot):
        budgets = {b['account_id']: b['amount_rappen'] for b in snapshot['budget']}
        rows = []
        for data in snapshot['accounts']:
            account = SimpleNamespace(**{**data, 'kind': AccountKind(data['kind'])})
            actual = sum(b['amount_rappen'] for b in snapshot['bookings'] if b['account_id'] == account.id)
            budget = budgets.get(account.id, 0)
            rows.append(dict(account=account, actual_rappen=actual, budget_rappen=budget, deviation_rappen=actual-budget))
        return rows

    @staticmethod
    def groups(snapshot):
        groups = {}
        for row in AccountingRevisionService.budget_rows(snapshot):
            account = row['account']
            key = (account.kind, account.group_name or 'Ohne Gruppe')
            group = groups.setdefault(key, dict(name=key[1], kind=account.kind, rows=[], budget_rappen=0, actual_rappen=0))
            group['rows'].append(row)
            group['budget_rappen'] += row['budget_rappen']
            group['actual_rappen'] += row['actual_rappen']
            group['deviation_rappen'] = group['actual_rappen'] - group['budget_rappen']
        return list(groups.values())

    @classmethod
    def opening_difference(cls, fy):
        snapshot = cls.active_snapshot(fy)
        if snapshot is None:
            return None
        return AccountingService.get_live_opening_balance(fy.id) - snapshot['opening_balance_rappen']

    @staticmethod
    def snapshot(fy):
        bookings = Booking.query.filter_by(fiscal_year_id=fy.id).order_by(Booking.id).all()
        budgets = BudgetEntry.query.filter_by(fiscal_year_id=fy.id).order_by(BudgetEntry.account_id).all()
        account_ids = {b.account_id for b in bookings} | {b.account_id for b in budgets}
        accounts = Account.query.filter(Account.id.in_(account_ids)).order_by(Account.id).all()
        return {
            'year': fy.year, 'start_date': fy.start_date.isoformat(), 'end_date': fy.end_date.isoformat(),
            'opening_balance_rappen': AccountingService.get_opening_balance(fy.id),
            'open_receipts': Receipt.query.filter(Receipt.booking_id.is_(None)).count(),
            'bookings': [dict(id=b.id, date=b.booking_date.isoformat(), description=b.description,
                              amount_rappen=b.amount_rappen, direction=b.direction.value,
                              account_id=b.account_id, member_id=b.member_id, event_id=b.event_id,
                              payment_ref=b.payment_ref) for b in bookings],
            'budget': [dict(account_id=b.account_id, amount_rappen=b.amount_rappen) for b in budgets],
            'accounts': [dict(id=a.id, code=a.code, name=a.name, kind=a.kind.value,
                              group_name=a.group_name) for a in accounts],
            'receipts': [dict(id=r.id, booking_id=r.booking_id, drive_file_id=r.drive_file_id,
                              name=r.label) for r in Receipt.query.filter(
                                  Receipt.booking_id.in_([b.id for b in bookings])).order_by(Receipt.id).all()],
        }

    @classmethod
    @atomic
    def submit(cls, year_id, actor, *, expected_version):
        cls.require_actor(actor, 'manage')
        fy = cls.lock(year_id, expected_version)
        if not fy.is_open:
            raise AccountingValidationError('Nur ein offenes Jahr kann vorgelegt werden.')
        revision = AccountingRevision(fiscal_year_id=fy.id, version=fy.review_version + 1,
                                      snapshot=cls.snapshot(fy), submitted_by=actor.id)
        db.session.add(revision)
        fy.review_version += 1
        fy.status = FiscalYearStatus.IN_REVIEW
        return fy

    @classmethod
    @atomic
    def withdraw(cls, year_id, actor, *, expected_version, reason, closed=False):
        cls.require_actor(actor, 'manage')
        reason = (reason or '').strip()
        if not reason or len(reason) > 2000:
            raise AccountingValidationError('Grund mit 1 bis 2000 Zeichen erforderlich.')
        fy = cls.lock(year_id, expected_version)
        if fy.status != (FiscalYearStatus.CLOSED if closed else FiscalYearStatus.IN_REVIEW):
            raise AccountingValidationError('Jahresstatus wurde geändert. Stand neu laden.')
        revision = cls.current(fy)
        if revision is None:
            # Record the legacy transition without inventing a historical snapshot/approval.
            fy.review_version += 1
            revision = AccountingRevision(fiscal_year_id=fy.id, version=fy.review_version,
                                          snapshot=None, submitted_by=actor.id)
            db.session.add(revision)
        revision.state = 'withdrawn'
        revision.withdrawn_by = actor.id
        revision.withdrawn_at = datetime.utcnow()
        revision.withdrawal_reason = reason
        fy.status = FiscalYearStatus.OPEN
        fy.closed_at = None
        return fy

    @classmethod
    @atomic
    def approve(cls, year_id, actor, *, expected_version):
        cls.require_actor(actor, 'approve')
        fy = cls.lock(year_id, expected_version)
        revision = cls.current(fy)
        if not fy.is_in_review or revision is None or revision.snapshot is None or revision.state != 'in_review':
            raise AccountingValidationError('Keine aktuelle Prüffassung. Altstand zurücknehmen und neu vorlegen.')
        if cls.opening_difference(fy):
            raise AccountingValidationError('Vorjahressaldo geändert. Zur Bearbeitung zurücknehmen und neu vorlegen.')
        if any(c.blocking and not c.resolved for c in AccountingService.get_comments_for_year(fy.id)):
            raise AccountingValidationError('Offene Beanstandungen verhindern die Bestätigung.')
        revision.state = 'approved'
        revision.reviewer_id = actor.id
        revision.reviewer_name = actor.display_name_with_spirit
        revision.approved_at = datetime.utcnow()
        revision.admin_substitute = actor.is_admin()
        fy.status = FiscalYearStatus.CLOSED
        fy.closed_at = revision.approved_at
        return fy

    @classmethod
    @atomic
    def comment(cls, year_id, actor, text, *, expected_version, booking_id=None, blocking=False):
        cls.require_actor(actor, 'comment')
        fy = cls.lock(year_id, expected_version)
        if fy.is_closed:
            raise AccountingValidationError('Abgeschlossener Prüfstand bleibt erhalten.')
        if not (text or '').strip():
            raise AccountingValidationError('Kommentar darf nicht leer sein.')
        if blocking:
            cls.require_actor(actor, 'approve')
            if not fy.is_in_review:
                raise AccountingValidationError('Beanstandung benötigt eine laufende Revision.')
        if booking_id is not None:
            booking = db.session.get(Booking, booking_id)
            if booking is None or booking.fiscal_year_id != fy.id:
                raise AccountingValidationError('Buchung gehört nicht zu diesem Jahr.')
        revision = cls.current(fy) if fy.is_in_review else None
        comment = RevisionComment(fiscal_year_id=fy.id, booking_id=booking_id, author_id=actor.id,
                                  text=text.strip(), revision_id=revision.id if revision else None,
                                  blocking=bool(blocking))
        db.session.add(comment)
        return comment

    @classmethod
    @atomic
    def resolve(cls, comment_id, actor, *, expected_version):
        cls.require_actor(actor, 'comment')
        comment = db.session.get(RevisionComment, comment_id)
        if comment is None:
            raise AccountingValidationError('Kommentar nicht gefunden.')
        year_id = comment.fiscal_year_id or comment.booking.fiscal_year_id
        fy = cls.lock(year_id, expected_version)
        comment = RevisionComment.query.filter_by(id=comment_id).populate_existing().with_for_update().one()
        if fy.is_closed or comment.resolved:
            raise AccountingValidationError('Kommentar ist abgeschlossen. Stand neu laden.')
        comment.resolved = True
        comment.resolved_by = actor.id
        comment.resolved_at = datetime.utcnow()
        return comment

    @classmethod
    @atomic
    def set_report(cls, year_id, report_drive_id, *, expected_version):
        # A delayed result belongs to its approved version, even after withdrawal.
        AccountingService.lock_fiscal_year(year_id)
        revision = AccountingRevision.query.filter_by(fiscal_year_id=year_id, version=expected_version).first()
        if revision is None or revision.approved_at is None or revision.report_drive_id:
            raise AccountingValidationError('Bericht kann dieser Fassung nicht zugeordnet werden.')
        revision.report_drive_id = report_drive_id
