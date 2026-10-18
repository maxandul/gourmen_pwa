from backend.models.participation import is_billbro_attending
from backend.services.billbro_state import BillBroStateService
"""Exact, deterministic shares; stored historical results remain authoritative."""
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from backend.extensions import db
from backend.models.event import Event
from backend.models.participation import Participation, Esstyp
from backend.models.accounting import MemberClaim
from backend.services.money import MoneyService
from backend.services.accounting import AccountingService
from backend.services.area_permissions import AreaPermissionService


class ShareError(ValueError):
    pass


class BillBroShareService:
    RULE = 'largest_remainder_rappen'
    GROUPS = ((Esstyp.SPARSAM, 'sparsam', 'Sparsam'),
              (Esstyp.NORMAL, 'normal', 'Normal'), (Esstyp.ALLIN, 'allin', 'All-In'))

    @staticmethod
    def distribute(total, weighted_members):
        if type(total) is not int or not 0 < total <= MoneyService.MAX_RAPPEN:
            raise ShareError('Gesamtbetrag liegt ausserhalb des gültigen Bereichs.')
        weights = {}
        for member_id, value in weighted_members:
            if type(member_id) is not int or member_id <= 0 or member_id in weights:
                raise ShareError('Teilnehmende sind nicht eindeutig zugeordnet.')
            try:
                text = str(value)
                if len(text) > 40:
                    raise ValueError()
                decimal = Decimal(text)
                if not decimal.is_finite() or decimal <= 0 or abs(decimal.adjusted()) > 100:
                    raise ValueError()
                weights[member_id] = Fraction(decimal)
            except (ValueError, InvalidOperation):
                raise ShareError('Ess-Typ-Gewichte müssen gültige positive Zahlen sein.') from None
        if not weights:
            raise ShareError('Mindestens eine anwesende Person ist erforderlich.')
        weight_sum = sum(weights.values())
        exact = {mid: total * weight / weight_sum for mid, weight in weights.items()}
        shares = {mid: value.numerator // value.denominator for mid, value in exact.items()}
        remaining = total - sum(shares.values())
        priority = sorted(shares, key=lambda mid: (-(exact[mid] - shares[mid]), mid))
        for mid in priority[:remaining]:
            shares[mid] += 1
        return shares

    @classmethod
    def calculate(cls, event, total):
        config = event.weights_used_json
        if not isinstance(config, dict):
            raise ShareError('Ess-Typ-Gewichte fehlen. Konfiguration prüfen.')
        keys = {kind: key for kind, key, _ in cls.GROUPS}
        members = []
        for part in event.participations:
            if is_billbro_attending(part):
                if part.esstyp not in keys:
                    raise ShareError('Für alle Anwesenden muss ein Ess-Typ vorliegen.')
                members.append((part.member_id, config.get(keys[part.esstyp])))
        return cls.distribute(total, members)

    @classmethod
    def apply(cls, event, total):
        shares = cls.calculate(event, total)
        for part in event.participations:
            part.calculated_share_rappen = shares.get(part.member_id) if is_billbro_attending(part) else None
        for kind, key, _ in cls.GROUPS:
            values = {shares[p.member_id] for p in event.participations if is_billbro_attending(p) and p.esstyp == kind}
            setattr(event, f'betrag_{key}_rappen', next(iter(values)) if len(values) == 1 else None)
        event.rounding_rule = cls.RULE
        return shares

    @classmethod
    def stored_share(cls, event, part):
        if part.calculated_share_rappen is not None:
            return part.calculated_share_rappen
        if event.rounding_rule != cls.RULE:
            for kind, key, _ in cls.GROUPS:
                if part.esstyp == kind:
                    return getattr(event, f'betrag_{key}_rappen')
        return None

    @classmethod
    def groups(cls, event):
        result = []
        for kind, key, label in cls.GROUPS:
            values = [cls.stored_share(event, p) for p in event.participations if is_billbro_attending(p) and p.esstyp == kind]
            values = [value for value in values if value is not None]
            result.append(dict(label=label, minimum=min(values) if values else None,
                               maximum=max(values) if values else None))
        return result

    @classmethod
    def finalize(cls, event, total, actor):
        """Own the first-finalization transaction, including initial claims."""
        invoice = event.rechnungsbetrag_rappen
        tip = event.trinkgeld_rappen
        try:
            event = Event.query.filter_by(id=event.id).populate_existing().with_for_update().one()
            if not AreaPermissionService.can_manage_event(actor, event) or not event.is_visible_to(actor):
                raise ShareError('Keine Berechtigung für diesen Abschluss.')
            if BillBroStateService.requires_correction(event):
                raise ShareError('Bereits abgeschlossen. Änderungen benötigen eine nachvollziehbare Korrektur.')
            if (invoice, tip) != (event.rechnungsbetrag_rappen, event.trinkgeld_rappen):
                raise ShareError('Rechnung wurde inzwischen geändert. Bitte neu prüfen.')
            if type(invoice) is not int or invoice <= 0 or total < invoice:
                raise ShareError('Gesamtbetrag darf die Rechnung nicht unterschreiten.')
            Participation.query.filter_by(event_id=event.id).populate_existing().with_for_update().all()
            if MemberClaim.query.filter_by(event_id=event.id).first():
                raise ShareError('Vorhandene Forderungen benötigen zuerst eine nachvollziehbare Korrektur.')
            for part in event.participations:
                if part.billbro_attendance is None:
                    part.billbro_attendance = part.billbro_attending
            cls.apply(event, total)
            event.gesamtbetrag_rappen = total
            event.trinkgeld_rappen = total - invoice
            AccountingService.create_claims_for_billbro(event, commit=False)
            db.session.commit()
        except ShareError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise ShareError('Abschluss konnte nicht gespeichert werden. Angaben bleiben erhalten.') from None
