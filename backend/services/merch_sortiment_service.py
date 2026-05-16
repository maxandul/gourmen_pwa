"""Merch v2 Sortiment (Lieferanten, Artikel, Varianten-Kombinatorik)."""

from __future__ import annotations

from itertools import product
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.merch_v2 import MerchArticle, MerchColor, MerchSize, MerchVariant
from backend.utils.merch_variant_key import (
    MERCH_COLOR_DIMENSION_KEYS_CF,
    MERCH_SIZE_DIMENSION_KEYS_CF,
    compute_merch_variant_key,
    normalized_attr_dimension_key,
    slugify_ascii_label,
)

MAX_VARIANT_DIMENSIONS = 6
MAX_OPTIONS_PER_DIMENSION = 24
MAX_OPTION_LABEL_LENGTH = 80
MAX_DIMENSION_KEY_LENGTH = 40
MAX_VARIANT_COMBINATIONS = 240


def _variant_schema_keys(schema: dict[str, list[Any]] | None) -> tuple[list[str], list[list[Any]]]:
    if not schema:
        return [], []
    keys = list(schema.keys())
    values = [schema[k] for k in keys]
    return keys, values


def attributes_match_key(attributes: dict[str, Any] | None, combo: dict[str, Any]) -> bool:
    """Vergleich normalisierter Schluessel/Werte (String)."""
    a = attributes or {}
    for k, v in combo.items():
        if str(a.get(k, '')) != str(v):
            return False
    keys_a = {str(x) for x in a.keys()}
    keys_c = {str(x) for x in combo.keys()}
    return keys_a == keys_c


def variant_schema_to_lines(schema: dict[str, list[Any]] | None) -> str:
    """Text fuer Textarea: je Zeile «dimension: a, b, c»."""
    if not schema:
        return ''
    lines: list[str] = []
    for dim, opts in schema.items():
        k = str(dim).strip()
        if not k:
            continue
        parts = [str(o).strip() for o in (opts or []) if str(o).strip()]
        if not parts:
            continue
        lines.append(f'{k}: ' + ', '.join(parts))
    return '\n'.join(lines)


def parse_variant_schema_text(raw: str | None) -> tuple[dict[str, list[str]] | None, str | None]:
    """Parst Stammdaten-Textarea; leer -> «ohne Dimensionen» (eine Standard-Variante).

    Returns:
        (schema, None) bei Erfolg, (None, fehlermeldung) bei Validierungsfehler.
    """
    if raw is None or not str(raw).strip():
        return {}, None

    seen_dims: set[str] = set()
    result: dict[str, list[str]] = {}

    for line_no, raw_line in enumerate(str(raw).splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if ':' not in line:
            return None, f'Zeile {line_no}: erwartet «dimension: option1, option2» (Doppelpunkt fehlt).'
        dim_part, rest = line.split(':', 1)
        dim = dim_part.strip()
        if not dim:
            return None, f'Zeile {line_no}: Dimensionsname fehlt.'
        if len(dim) > MAX_DIMENSION_KEY_LENGTH:
            return None, (
                f'Zeile {line_no}: Dimensionsname zu lang (max. {MAX_DIMENSION_KEY_LENGTH} Zeichen).'
            )
        low = dim.casefold()
        if low in seen_dims:
            return None, f'Zeile {line_no}: Dimension «{dim}» ist bereits definiert.'
        seen_dims.add(low)

        tokens = [t.strip() for t in rest.split(',')]
        opts: list[str] = []
        seen_opt: set[str] = set()
        for t in tokens:
            if not t:
                continue
            if len(t) > MAX_OPTION_LABEL_LENGTH:
                return None, (
                    f'Zeile {line_no}: Option zu lang '
                    f'(max. {MAX_OPTION_LABEL_LENGTH} Zeichen).'
                )
            tl = t.casefold()
            if tl not in seen_opt:
                seen_opt.add(tl)
                opts.append(t)
        if not opts:
            return None, f'Zeile {line_no}: mindestens eine Option angeben.'

        if len(opts) > MAX_OPTIONS_PER_DIMENSION:
            return None, (
                f'Zeile {line_no}: maximal {MAX_OPTIONS_PER_DIMENSION} Optionen pro Dimension.'
            )

        result[dim] = opts

    if len(result) > MAX_VARIANT_DIMENSIONS:
        return None, f'Maximal {MAX_VARIANT_DIMENSIONS} Dimensionen erlaubt.'

    combo_count = 1
    for opts in result.values():
        combo_count *= len(opts)
    if combo_count > MAX_VARIANT_COMBINATIONS:
        return (
            None,
            f'Zu viele Varianten-Kombinationen ({combo_count}); '
            f'bitte Schema vereinfachen (Grenze {MAX_VARIANT_COMBINATIONS}).',
        )

    return result, None


def _combo_dimension_label(
    combo: dict[str, Any], dim_keys_cf: frozenset[str]
) -> str | None:
    for k_raw, val in combo.items():
        if normalized_attr_dimension_key(str(k_raw)) not in dim_keys_cf:
            continue
        lbl = str(val).strip()
        if lbl:
            return lbl[:160]
    return None


def _ensure_merch_color_id(label: str | None) -> int | None:
    if not label or not label.strip():
        return None
    base_slug = slugify_ascii_label(label)
    slug_try = base_slug
    suffix = 2
    while True:
        row = MerchColor.query.filter_by(slug=slug_try).first()
        if row is not None:
            return row.id
        try:
            with db.session.begin_nested():
                nxt_sort = db.session.scalar(
                    func.coalesce(func.max(MerchColor.sort_order), 0)
                )
                mc = MerchColor(
                    slug=slug_try,
                    label=str(label).strip()[:160],
                    sort_order=int(nxt_sort or 0) + 1,
                )
                db.session.add(mc)
                db.session.flush()
                return mc.id
        except IntegrityError:
            slug_try = f'{base_slug}-{suffix}'
            suffix += 1


def _ensure_merch_size_id(label: str | None) -> int | None:
    if not label or not label.strip():
        return None
    slug = slugify_ascii_label(label)
    row = MerchSize.query.filter_by(slug=slug).first()
    if row is not None:
        return row.id
    try:
        with db.session.begin_nested():
            nxt_sort = db.session.scalar(
                func.coalesce(func.max(MerchSize.sort_order), 0)
            )
            ms = MerchSize(
                slug=slug,
                label=str(label).strip()[:160],
                sort_order=int(nxt_sort or 0) + 1,
            )
            db.session.add(ms)
            db.session.flush()
            return ms.id
    except IntegrityError:
        row2 = MerchSize.query.filter_by(slug=slug).first()
        if row2 is not None:
            return row2.id
        raise


def _apply_variant_physical_fields(variant: MerchVariant, combo: dict[str, Any]) -> None:
    attrs_cd = dict(combo)
    c_lbl = _combo_dimension_label(attrs_cd, MERCH_COLOR_DIMENSION_KEYS_CF)
    s_lbl = _combo_dimension_label(attrs_cd, MERCH_SIZE_DIMENSION_KEYS_CF)
    variant.color_id = _ensure_merch_color_id(c_lbl)
    variant.size_id = _ensure_merch_size_id(s_lbl)
    variant.variant_key = compute_merch_variant_key(
        color_id=variant.color_id,
        size_id=variant.size_id,
        attributes=attrs_cd,
    )[:126]


class MerchSortimentService:
    """Kombinationen aus variant_schema; Listenpreis-Aufloesung."""

    @staticmethod
    def sync_variants_for_article(article: MerchArticle, schema: dict[str, list[str]] | None) -> None:
        """Abgleicht DB-Varianten mit Schema-Kombinatorik; nicht mehr passende werden deaktiviert.

        Keine DELETE-Zeilen (FKs aus Runden/Bestellungen bleiben gueltig).
        """
        normalized: dict[str, list[str]] = dict(schema) if schema else {}
        article.variant_schema = normalized or {}
        combos = MerchSortimentService.variant_attribute_combinations(
            normalized if normalized else None
        )

        def norm_key(attrs: dict[str, Any] | None) -> tuple[tuple[str, str], ...]:
            a = attrs or {}
            return tuple(sorted((str(k), str(v)) for k, v in a.items()))

        wanted_keys = {norm_key(c) for c in combos}

        existing = (
            MerchVariant.query.filter_by(article_id=article.id)
            .order_by(MerchVariant.id.asc())
            .all()
        )

        matched_ids: set[int] = set()

        for combo in combos:
            hit: MerchVariant | None = None
            for v in existing:
                if v.id in matched_ids:
                    continue
                if attributes_match_key(v.attributes, combo):
                    hit = v
                    break
            if hit:
                hit.is_active = True
                cd = dict(combo)
                if hit.attributes != cd:
                    hit.attributes = cd
                _apply_variant_physical_fields(hit, cd)
                if hit.id:
                    matched_ids.add(hit.id)
            else:
                cd = dict(combo)
                nv = MerchVariant(
                    article_id=article.id,
                    attributes=cd,
                    is_active=True,
                )
                _apply_variant_physical_fields(nv, cd)
                db.session.add(nv)

        for v in existing:
            if v.id and norm_key(v.attributes) not in wanted_keys:
                v.is_active = False

    @staticmethod
    def variant_attribute_combinations(
        variant_schema: dict[str, list[Any]] | None,
    ) -> list[dict[str, Any]]:
        """Leeres Schema -> eine Variante ohne Dimensionen (`{}`)."""
        keys, values = _variant_schema_keys(variant_schema)
        if not keys:
            return [{}]
        return [dict(zip(keys, combo)) for combo in product(*values)]

    @staticmethod
    def list_price_rappen_for_variant(article: MerchArticle, variant: MerchVariant) -> int:
        """Variantenpreis oder Fallback auf Artikel-Listenpreis."""
        if variant.list_price_rappen is not None:
            return variant.list_price_rappen
        return article.list_price_rappen
