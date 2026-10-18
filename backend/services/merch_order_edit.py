"""Quantity edits preserve bound item prices; definitive pricing is separate."""
import hashlib
import json
import re
from collections import defaultdict
from itertools import zip_longest

from backend.extensions import db
from backend.models.merch_article import MerchArticle
from backend.models.merch_order import MerchOrder, OrderStatus
from backend.models.merch_order_item import MerchOrderItem
from backend.models.accounting import MemberClaim
from backend.services.merch_catalogue import catalogue_context
from backend.services.merch_variants import MerchVariantService
from backend.services.money import MoneyService


class OrderEditError(ValueError):
    pass


class MerchOrderEditService:
    @staticmethod
    def context(order):
        context = catalogue_context()
        articles = {article.id: article for article in context['articles']}
        variants = context['catalogue_variants']
        items = defaultdict(list)
        bound = {}
        for item in order.order_items:
            articles[item.article_id] = item.article
            rows = variants.setdefault(item.article_id, [])
            if not any(v.id == item.variant_id for v in rows):
                rows.append(item.variant)
            prices = (item.unit_member_price_rappen, item.unit_supplier_price_rappen)
            if item.variant_id in bound and bound[item.variant_id] != prices:
                raise OrderEditError('Diese Bestellung enthält unterschiedliche Preise derselben Ausführung. Bitte mit Merch-Verantwortlichen klären.')
            bound[item.variant_id] = prices
            items[item.article_id].append(dict(color=item.variant.color, size=item.variant.size, quantity=item.quantity))
        projected = {}
        for aid, rows in variants.items():
            projected[aid] = [dict(id=v.id, color=v.color, size=v.size,
                                  member_price_rappen=bound.get(v.id, (v.member_price_rappen, v.supplier_price_rappen))[0],
                                  supplier_price_rappen=bound.get(v.id, (v.member_price_rappen, v.supplier_price_rappen))[1],
                                  is_active=v.is_active and articles[aid].is_active) for v in rows]
        state = [order.id, order.status.value,
                 [order.total_member_price_rappen, order.total_supplier_price_rappen, order.total_profit_rappen],
                 sorted((i.id, i.variant_id, i.quantity, i.unit_member_price_rappen, i.unit_supplier_price_rappen,
                         i.description_snapshot, i.description_snapshot_source) for i in order.order_items),
                 projected]
        context.update(articles=list(articles.values()), catalogue_variants=projected,
                       catalogue_colors={aid: sorted({v['color'] for v in rows}) for aid, rows in projected.items()},
                       existing_items=dict(items), order_edit_version=hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest())
        return context

    @staticmethod
    def posted_items(form):
        result = {}
        for key in form:
            match = re.fullmatch(r'color_([0-9]+)\[\]', key)
            if match:
                aid = int(match[1])
                result[aid] = [dict(color=color, size=size, quantity=quantity)
                               for color, size, quantity in zip_longest(form.getlist(key), form.getlist(f'size_{aid}[]'),
                                                                        form.getlist(f'quantity_{aid}[]'), fillvalue='')]
        return result

    @classmethod
    def save(cls, order_id, actor, form):
        try:
            order = MerchOrder.query.filter_by(id=order_id, member_id=actor.id).populate_existing().with_for_update().one()
            if not actor.is_active or order.status != OrderStatus.BESTELLT:
                raise OrderEditError('Bestellung ist nicht mehr zur Bearbeitung offen.')
            aids = {item.article_id for item in order.order_items}
            for key in form:
                match = re.fullmatch(r'(?:color|size|quantity)_([0-9]+)\[\]', key)
                if match:
                    aids.add(int(match[1]))
            MerchArticle.query.filter(MerchArticle.id.in_(aids)).order_by(MerchArticle.id).populate_existing().with_for_update().all()
            MerchOrderItem.query.filter_by(order_id=order.id).populate_existing().with_for_update().all()
            db.session.expire(order, ['order_items'])
            context = cls.context(order)
            available = {v['id']: v for rows in context['catalogue_variants'].values() for v in rows}
            existing = defaultdict(list)
            for item in order.order_items:
                existing[item.variant_id].append(item)
            old_quantities = {vid: sum(i.quantity for i in rows) for vid, rows in existing.items()}
            requested = defaultdict(int)
            variant_articles = {}
            for aid in aids:
                colors, sizes, quantities = (form.getlist(f'{field}_{aid}[]') for field in ('color', 'size', 'quantity'))
                if not len(colors) == len(sizes) == len(quantities):
                    raise OrderEditError('Auswahl ist unvollständig. Farbe, Grösse und Menge je Zeile prüfen.')
                for color, size, raw in zip(colors, sizes, quantities):
                    if not re.fullmatch(r'[0-9]{1,10}', str(raw or '0')) or int(raw or '0') > MoneyService.MAX_RAPPEN:
                        raise OrderEditError('Menge muss eine nichtnegative ganze Zahl im gültigen Bereich sein.')
                    quantity = int(raw or '0')
                    if quantity == 0:
                        continue
                    matches = [v for v in context['catalogue_variants'].get(aid, [])
                               if (MerchVariantService.label(v['color']).casefold(), MerchVariantService.label(v['size']).casefold()) ==
                               (MerchVariantService.label(color).casefold(), MerchVariantService.label(size).casefold())]
                    if len(matches) != 1:
                        raise OrderEditError('Ausführung ist nicht eindeutig oder nicht verfügbar. Auswahl prüfen.')
                    variant = matches[0]
                    requested[variant['id']] += quantity
                    variant_articles[variant['id']] = aid
            if dict(requested) == old_quantities:
                db.session.rollback()
                return False
            if not requested:
                raise OrderEditError('Eine leere Bestellung benötigt einen ausdrücklichen Stornoweg. Bitte mit Merch-Verantwortlichen klären.')
            if form.get('order_edit_version') != context['order_edit_version']:
                raise OrderEditError('Bestellung oder Preise wurden inzwischen geändert. Angaben und Preise neu prüfen und erneut speichern.')
            if MemberClaim.query.filter_by(merch_order_id=order.id).first():
                raise OrderEditError('Für diese Bestellung besteht bereits eine Forderung. Änderung mit Merch-Verantwortlichen und Schatzmeister klären.')
            items = list(order.order_items)
            if any((item.total_member_price_rappen, item.total_supplier_price_rappen, item.total_profit_rappen) !=
                   (item.quantity * item.unit_member_price_rappen, item.quantity * item.unit_supplier_price_rappen,
                    item.quantity * (item.unit_member_price_rappen - item.unit_supplier_price_rappen)) for item in items) or (
                    order.total_member_price_rappen, order.total_supplier_price_rappen, order.total_profit_rappen) != (
                    sum(item.total_member_price_rappen for item in items),
                    sum(item.total_supplier_price_rappen for item in items), sum(item.total_profit_rappen for item in items)):
                raise OrderEditError('Bestehende Bestellbeträge sind widersprüchlich. Bitte zuerst mit Merch-Verantwortlichen klären.')
            for vid, quantity in requested.items():
                if quantity > MoneyService.MAX_RAPPEN:
                    raise OrderEditError('Gesamtmenge dieser Ausführung liegt ausserhalb des gültigen Bereichs.')
                if not available[vid]['is_active'] and quantity > old_quantities.get(vid, 0):
                    raise OrderEditError('Nicht mehr angebotene Ausführungen können nicht erhöht werden.')
                if len(existing.get(vid, [])) > 1 and quantity != old_quantities[vid]:
                    raise OrderEditError('Mehrere alte Positionen derselben Ausführung müssen zuerst geklärt werden.')
            member_total = sum(quantity * available[vid]['member_price_rappen'] for vid, quantity in requested.items())
            supplier_total = sum(quantity * available[vid]['supplier_price_rappen'] for vid, quantity in requested.items())
            if any(available[vid]['member_price_rappen'] < 0 or available[vid]['supplier_price_rappen'] < 0 for vid in requested) or not all(0 <= total <= MoneyService.MAX_RAPPEN for total in (member_total, supplier_total)):
                raise OrderEditError('Bestellbetrag liegt ausserhalb des gültigen Bereichs.')
            for vid, rows in existing.items():
                if vid not in requested:
                    for item in rows:
                        db.session.delete(item)
                elif requested[vid] != old_quantities[vid]:
                    rows[0].quantity = requested[vid]
                    rows[0].calculate_totals()
            for vid in requested.keys() - existing.keys():
                from backend.models.merch_variant import MerchVariant
                variant = db.session.get(MerchVariant, vid)
                item = MerchOrderItem(order_id=order.id, article_id=variant_articles[vid], variant_id=vid,
                                      quantity=requested[vid], unit_member_price_rappen=available[vid]['member_price_rappen'],
                                      unit_supplier_price_rappen=available[vid]['supplier_price_rappen'])
                item.article = variant.article
                item.variant = variant
                item.capture_description()
                item.calculate_totals()
                db.session.add(item)
            order.total_member_price_rappen = member_total
            order.total_supplier_price_rappen = supplier_total
            order.total_profit_rappen = member_total - supplier_total
            db.session.commit()
            return True
        except OrderEditError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise OrderEditError('Bestellung konnte nicht gespeichert werden. Angaben bleiben erhalten.') from None
