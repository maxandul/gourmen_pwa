"""Deterministische `variant_key` fuer UNIQUE (article_id, variant_key).

Spezifikation: `docs/capabilities/merch-article-variant-target-state.md` §8.1.

- Sobald eine Farbe- und/oder Grössen-FK gesetzt ist, beginnt der Schluessel mit
  einem FK-Teil. Zusaetzliche Attribut-Schluessel (nicht Farbe/Groesse) werden
  gehasht angehaengt, damit Kombinationen mit gleicher Farbe/Groesse trotzdem
  unterscheidbar bleiben.
- Reine JSON-Dimensionen ohne FK: kanonisches JSON; bei Laenge wird gehasht.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

# NFKC+casefold — gleiche Konstanten in Migration c4e8a9012b71 pflegen/hier anpassen
MERCH_COLOR_DIMENSION_KEYS_CF = frozenset({'farbe', 'color'})
MERCH_SIZE_DIMENSION_KEYS_CF = frozenset(
    {
        'groesse',
        'groessen',
        'grösse',
        'grössen',
        'size',
        'sizes',
    }
)


def normalized_attr_dimension_key(raw_key: str) -> str:
    return unicodedata.normalize('NFKC', str(raw_key)).strip().casefold()


def extra_dimensions_json(attributes: dict | None) -> dict[str, str]:
    """Alle Attribute ausser klassischer Farbe/Groesse (fuer Zusatz im variant_key)."""
    out: dict[str, str] = {}
    for k, v in (attributes or {}).items():
        nk = normalized_attr_dimension_key(k)
        if nk in MERCH_COLOR_DIMENSION_KEYS_CF or nk in MERCH_SIZE_DIMENSION_KEYS_CF:
            continue
        out[str(k)] = str(v)
    return dict(sorted(out.items()))


def _extras_digest(extra: dict[str, str]) -> str:
    if not extra:
        return ''
    raw = json.dumps(
        extra,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':'),
    )
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]


def compute_merch_variant_key(
    *,
    color_id: int | None,
    size_id: int | None,
    attributes: dict | None,
) -> str:
    extra = extra_dimensions_json(attributes)
    ex_sig = _extras_digest(extra)

    if color_id is not None or size_id is not None:
        c = '-' if color_id is None else str(int(color_id))
        s = '-' if size_id is None else str(int(size_id))
        base = f'fk|c={c}|s={s}'
        if ex_sig:
            return f'{base}|x:{ex_sig}'
        return base

    attrs = attributes or {}
    if not attrs:
        return 'js|{}'

    raw = json.dumps(attrs, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    if len(raw) <= 112:
        return f'js|{raw}'
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:56]
    return f'jh|{digest}'


_WS_RE = re.compile(r'\s+')
_NON_ALNUM = re.compile(r'[^a-z0-9\-]+')


def slugify_ascii_label(label: str, *, max_len: int = 80) -> str:
    """Slug fuer Lookup-Tabellen (ASCII). Leer oder ungueltig -> `stueck`."""
    t = unicodedata.normalize('NFKC', str(label)).strip().lower()
    trans = str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'})
    t = t.translate(trans)
    t = ''.join(c if c.isalnum() or c in '- ' else '-' for c in t)
    t = _WS_RE.sub('-', t)
    t = _NON_ALNUM.sub('-', t)
    t = re.sub(r'-{2,}', '-', t).strip('-')
    if not t:
        return 'stueck'
    if len(t) > max_len:
        t = t[:max_len].rstrip('-')
    return t or 'stueck'
