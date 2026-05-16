"""Merch v2: globale Stammdaten Farbe/Groesse (Lookups ohne Deaktivierungs-Flag).

Neue Eintraege und Umbenennen (Label) fuer Marketingchef/Admin gem.
`docs/capabilities/merch-article-variant-target-state.md`.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.merch_v2 import MerchColor, MerchSize, MerchVariant
from backend.utils.merch_variant_key import slugify_ascii_label


class MerchLookupService:
    @staticmethod
    def list_colors_ordered() -> list[MerchColor]:
        return (
            MerchColor.query.order_by(MerchColor.sort_order.asc(), MerchColor.label.asc())
            .all()
        )

    @staticmethod
    def list_sizes_ordered() -> list[MerchSize]:
        return (
            MerchSize.query.order_by(MerchSize.sort_order.asc(), MerchSize.label.asc())
            .all()
        )

    @staticmethod
    def create_color(label_raw: str) -> dict:
        lbl = str(label_raw or '').strip()[:160]
        if len(lbl) < 1:
            return {'success': False, 'error': 'Bezeichnung fehlt.'}
        base_slug = slugify_ascii_label(lbl)
        slug_try = base_slug
        suffix = 2
        while True:
            existing = MerchColor.query.filter_by(slug=slug_try).first()
            if existing is not None:
                if slug_try == base_slug:
                    return {
                        'success': False,
                        'error': f'Eine Farbe mit gleichem Kurzcode existiert bereits («{existing.label}»).',
                    }
                slug_try = f'{base_slug}-{suffix}'
                suffix += 1
                continue
            try:
                with db.session.begin_nested():
                    mx = db.session.scalar(
                        func.coalesce(func.max(MerchColor.sort_order), 0)
                    )
                    row = MerchColor(
                        slug=slug_try,
                        label=lbl,
                        sort_order=int(mx or 0) + 1,
                    )
                    db.session.add(row)
                    db.session.flush()
                return {'success': True, 'row': row}
            except IntegrityError:
                slug_try = f'{base_slug}-{suffix}'
                suffix += 1

    @staticmethod
    def create_size(label_raw: str) -> dict:
        lbl = str(label_raw or '').strip()[:160]
        if len(lbl) < 1:
            return {'success': False, 'error': 'Bezeichnung fehlt.'}
        base_slug = slugify_ascii_label(lbl)
        slug_try = base_slug
        suffix = 2
        while True:
            existing = MerchSize.query.filter_by(slug=slug_try).first()
            if existing is not None:
                if slug_try == base_slug:
                    return {
                        'success': False,
                        'error': f'Eine Grösse mit gleichem Kurzcode existiert bereits («{existing.label}»).',
                    }
                slug_try = f'{base_slug}-{suffix}'
                suffix += 1
                continue
            try:
                with db.session.begin_nested():
                    mx = db.session.scalar(
                        func.coalesce(func.max(MerchSize.sort_order), 0)
                    )
                    row = MerchSize(
                        slug=slug_try,
                        label=lbl,
                        sort_order=int(mx or 0) + 1,
                    )
                    db.session.add(row)
                    db.session.flush()
                return {'success': True, 'row': row}
            except IntegrityError:
                slug_try = f'{base_slug}-{suffix}'
                suffix += 1

    @staticmethod
    def rename_color(color_id: int, new_label_raw: str) -> dict:
        lbl = str(new_label_raw or '').strip()[:160]
        if len(lbl) < 1:
            return {'success': False, 'error': 'Bezeichnung fehlt.'}
        row = db.session.get(MerchColor, color_id)
        if row is None:
            return {'success': False, 'error': 'Farbe nicht gefunden.'}
        row.label = lbl
        return {'success': True}

    @staticmethod
    def rename_size(size_id: int, new_label_raw: str) -> dict:
        lbl = str(new_label_raw or '').strip()[:160]
        if len(lbl) < 1:
            return {'success': False, 'error': 'Bezeichnung fehlt.'}
        row = db.session.get(MerchSize, size_id)
        if row is None:
            return {'success': False, 'error': 'Grösse nicht gefunden.'}
        row.label = lbl
        return {'success': True}


class MerchVariantBulkService:
    """Bulk-Aktionen auf Variantenebene fuer einen Artikel."""

    @staticmethod
    def deactivate_variants_with_color(
        *, article_id: int, color_id: int
    ) -> tuple[int, str | None]:
        if color_id <= 0:
            return 0, 'Ungültige Farbe.'
        n = MerchVariant.query.filter_by(
            article_id=article_id, color_id=color_id
        ).update({'is_active': False}, synchronize_session=False)
        return int(n or 0), None

    @staticmethod
    def deactivate_variants_with_size(
        *, article_id: int, size_id: int
    ) -> tuple[int, str | None]:
        if size_id <= 0:
            return 0, 'Ungültige Grösse.'
        n = MerchVariant.query.filter_by(
            article_id=article_id, size_id=size_id
        ).update({'is_active': False}, synchronize_session=False)
        return int(n or 0), None
