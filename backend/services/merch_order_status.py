"""Atomic forward status transitions without rewriting financial history."""
from datetime import datetime

from backend.extensions import db
from backend.models.merch_order import MerchOrder, OrderStatus
from backend.models.merch_order_item import MerchOrderItem
from backend.models.accounting import MemberClaim, ClaimType
from backend.services.accounting import AccountingService
from backend.services.area_permissions import AreaPermissionService
from backend.services.money import MoneyService


class MerchStatusError(ValueError):
    pass


class MerchOrderStatusService:
    @staticmethod
    def change(order_id, actor, target):
        try:
            if not AreaPermissionService.has_scope(actor, 'merch_manage'):
                raise MerchStatusError('Keine Berechtigung für die Merch-Verwaltung.')
            try:
                target = OrderStatus(target)
            except (ValueError, TypeError):
                raise MerchStatusError('Ungültiger Status.') from None
            order = MerchOrder.query.filter_by(id=order_id).populate_existing().with_for_update().one()
            if target == order.status:
                db.session.rollback()
                return False
            sequence = [OrderStatus.BESTELLT, OrderStatus.WIRD_GELIEFERT, OrderStatus.GELIEFERT]
            if sequence.index(target) < sequence.index(order.status):
                raise MerchStatusError('Rückschritte benötigen einen eigenen Korrekturweg. Bestellung und Zahlungen bleiben unverändert.')
            items = MerchOrderItem.query.filter_by(order_id=order.id).populate_existing().with_for_update().all()
            if not items or any(not 1 <= item.quantity <= MoneyService.MAX_RAPPEN or
                                not 0 <= item.unit_member_price_rappen <= MoneyService.MAX_RAPPEN or
                                not 0 <= item.unit_supplier_price_rappen <= MoneyService.MAX_RAPPEN or
                                (item.total_member_price_rappen, item.total_supplier_price_rappen, item.total_profit_rappen) !=
                                (item.quantity * item.unit_member_price_rappen, item.quantity * item.unit_supplier_price_rappen,
                                 item.quantity * (item.unit_member_price_rappen - item.unit_supplier_price_rappen)) for item in items):
                raise MerchStatusError('Bestellpositionen sind unvollständig oder widersprüchlich. Bitte zuerst klären.')
            totals = (sum(i.total_member_price_rappen for i in items), sum(i.total_supplier_price_rappen for i in items),
                      sum(i.total_profit_rappen for i in items))
            if (order.total_member_price_rappen, order.total_supplier_price_rappen, order.total_profit_rappen) != totals or not all(
                    0 <= total <= MoneyService.MAX_RAPPEN for total in totals[:2]):
                raise MerchStatusError('Bestellbeträge sind widersprüchlich oder zu gross. Bitte zuerst klären.')
            claims = MemberClaim.query.filter_by(merch_order_id=order.id).populate_existing().with_for_update().all()
            if len(claims) > 1 or any(claim.claim_type != ClaimType.MERCH or claim.member_id != order.member_id or
                                      claim.creditor_member_id is not None or claim.event_id is not None or
                                      claim.expected_rappen != order.total_member_price_rappen for claim in claims):
                raise MerchStatusError('Bestehende Forderung passt nicht eindeutig zur Bestellung. Bitte mit dem Schatzmeister klären.')
            order.status = target
            if target == OrderStatus.GELIEFERT and order.delivered_at is None:
                order.delivered_at = datetime.utcnow()
            AccountingService.create_claim_for_merch_order(order, commit=False)
            db.session.commit()
            return True
        except MerchStatusError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise MerchStatusError('Status konnte nicht gespeichert werden. Bestellung und Forderung bleiben unverändert.') from None
