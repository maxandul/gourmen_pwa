"""Stable variant identities and retained order descriptions during catalogue edits."""
import unicodedata

from backend.extensions import db
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
from backend.models.merch_order_item import MerchOrderItem
from backend.services.area_permissions import AreaPermissionService
from backend.services.merch_prices import MerchPriceService, MerchPriceError


class MerchCatalogueError(MerchPriceError):
    pass


class MerchVariantService:
    @staticmethod
    def label(value):
        return unicodedata.normalize('NFC', ' '.join(str(value).split()))

    @classmethod
    def choices(cls, values, field, maximum):
        result = {}
        for value in values:
            label = cls.label(value)
            if not label or len(label) > maximum:
                raise MerchCatalogueError({field: f'Alle Angaben müssen 1 bis {maximum} Zeichen enthalten.'})
            result.setdefault(label.casefold(), label)
        if not result:
            raise MerchCatalogueError({field: 'Mindestens einen Wert angeben.'})
        return result

    @classmethod
    def find_active(cls, article_id, color, size):
        key = (cls.label(color).casefold(), cls.label(size).casefold())
        matches = [variant for variant in MerchVariant.query.filter_by(article_id=article_id, is_active=True).all()
                   if (cls.label(variant.color).casefold(), cls.label(variant.size).casefold()) == key]
        if len(matches) > 1:
            raise ValueError('Ausführung ist nicht eindeutig. Merch-Verantwortliche müssen die Zuordnung zuerst klären.')
        return matches[0] if matches else None

    @classmethod
    def save(cls, form, actor, article_id=None):
        try:
            if not AreaPermissionService.has_scope(actor, 'merch_manage'):
                raise MerchCatalogueError({'catalogue': 'Keine Berechtigung für Artikelpflege.'})
            supplier, member = MerchPriceService.form_prices(form)
            colors = cls.choices(form.getlist('colors'), 'colors', 50)
            sizes = cls.choices(form.getlist('sizes'), 'sizes', 20)
            name = cls.label(form.get('name', ''))
            if not name or len(name) > 200:
                raise MerchCatalogueError({'name': 'Artikelname muss 1 bis 200 Zeichen enthalten.'})
            if article_id is None:
                article = MerchArticle()
                existing = []
            else:
                article = MerchArticle.query.filter_by(id=article_id).populate_existing().with_for_update().one()
                existing = MerchVariant.query.filter_by(article_id=article.id).order_by(MerchVariant.id).with_for_update().all()
            by_key = {}
            for variant in existing:
                key = (cls.label(variant.color).casefold(), cls.label(variant.size).casefold())
                if key in by_key:
                    raise MerchCatalogueError({'catalogue': 'Dieser Artikel enthält mehrdeutige alte Varianten. Zuordnung zuerst klären; es wurde nichts geändert.'})
                by_key[key] = variant
            if article_id is not None:
                for item in MerchOrderItem.query.filter_by(article_id=article.id).with_for_update().all():
                    if item.description_snapshot is None:
                        item.capture_description(legacy=True)
            article.name = name
            article.description = form.get('description')
            article.image_url = form.get('image_url') or None
            article.is_active = form.get('is_active') == 'on'
            article.base_supplier_price_rappen = supplier
            article.base_member_price_rappen = member
            db.session.add(article)
            db.session.flush()
            selected = {(color, size) for color in colors for size in sizes}
            for key, variant in by_key.items():
                variant.is_active = key in selected
            for color, size in sorted(selected):
                if (color, size) not in by_key:
                    db.session.add(MerchVariant(article_id=article.id, color=colors[color], size=sizes[size],
                                               supplier_price_rappen=supplier, member_price_rappen=member,
                                               is_active=True))
            db.session.commit()
            return article, len(selected)
        except MerchPriceError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise MerchCatalogueError({'catalogue': 'Artikel konnte nicht gespeichert werden. Angaben bleiben erhalten.'}) from None
