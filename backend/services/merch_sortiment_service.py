"""Merch v2 Sortiment (Lieferanten, Artikel, Varianten-Kombinatorik)."""

from __future__ import annotations

from itertools import product
from typing import Any

from backend.models.merch_v2 import MerchArticle, MerchVariant


def _variant_schema_keys(schema: dict[str, list[Any]] | None) -> tuple[list[str], list[list[Any]]]:
    if not schema:
        return [], []
    keys = list(schema.keys())
    values = [schema[k] for k in keys]
    return keys, values


class MerchSortimentService:
    """Kombinationen aus variant_schema; Listenpreis-Aufloesung."""

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
