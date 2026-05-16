"""Merch Farbe/Groesse Lookups, variant_key, FKs auf merch_variants.

Revision ID: c4e8a9012b71
Revises: b7c2e8f91d04

Synchron mit `backend/utils/merch_variant_key.py`:
`normalized_attr_dimension_key`, `extra_dimensions_json`, Digest-Laenge fuer `|x:|`.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

import sqlalchemy as sa
from alembic import op
from sqlalchemy.exc import IntegrityError

revision = 'c4e8a9012b71'
down_revision = 'b7c2e8f91d04'
branch_labels = None
depends_on = None

_COLOR_KEYS_CF = frozenset({'farbe', 'color'})
_SIZE_KEYS_CF = frozenset(
    {'groesse', 'groessen', 'grösse', 'grössen', 'size', 'sizes'}
)


def _norm_dim_key(raw_key: str) -> str:
    return unicodedata.normalize('NFKC', str(raw_key)).strip().casefold()


def _extra_dimensions_json(attributes: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in attributes.items():
        nk = _norm_dim_key(k)
        if nk in _COLOR_KEYS_CF or nk in _SIZE_KEYS_CF:
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


def _compute_variant_key_migration(
    color_id_val,
    size_id_val,
    attrs: dict,
) -> str:
    cid = None if color_id_val is None else int(color_id_val)
    sid = None if size_id_val is None else int(size_id_val)
    extras = _extras_digest(_extra_dimensions_json(attrs))
    if cid is not None or sid is not None:
        c = '-' if cid is None else str(cid)
        s = '-' if sid is None else str(sid)
        base = f'fk|c={c}|s={s}'
        if extras:
            return f'{base}|x:{extras}'
        return base
    if not attrs:
        return 'js|{}'
    raw = json.dumps(
        attrs, sort_keys=True, ensure_ascii=False, separators=(',', ':')
    )
    if len(raw) <= 112:
        return f'js|{raw}'
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:56]
    return f'jh|{digest}'


_WS_RE = re.compile(r'\s+')
_NON_ALNUM = re.compile(r'[^a-z0-9\-]+')


def _slugify_ascii_label(label: str, *, max_len: int = 80) -> str:
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


def _attrs_dict(raw) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    try:
        return dict(raw)
    except (TypeError, ValueError):
        return {}


def _pick_dimension(attrs: dict, keyset_cf: frozenset[str]):
    for k, v in attrs.items():
        if _norm_dim_key(k) in keyset_cf:
            val = str(v).strip()
            if val:
                return val
    return None


def _finalize_unique_variant_keys(conn):
    """Kollisionsaufloesung: `(article_id, variant_key)` muss vor Unique-Constraint einzigartig sein."""
    rows = conn.execute(
        sa.text(
            'SELECT id, article_id, variant_key FROM merch_variants ORDER BY id ASC'
        )
    ).fetchall()
    buckets: dict[tuple[int, str], list[int]] = {}
    for vid, aid, vk in rows:
        if vk is None:
            continue
        buckets.setdefault((int(aid), str(vk)), []).append(int(vid))
    for (_aid, vk), ids in buckets.items():
        if len(ids) < 2:
            continue
        for vid in ids[1:]:
            nk = f'{vk}|i{vid}'
            nk = nk[:126]
            conn.execute(
                sa.text('UPDATE merch_variants SET variant_key=:nk WHERE id=:id'),
                {'nk': nk, 'id': vid},
            )


def _seed_default_sizes(conn) -> None:
    n = conn.scalar(sa.text('SELECT COUNT(*) FROM merch_sizes'))
    if n and int(n) > 0:
        return
    rows = [
        ('s', 'S', 10),
        ('m', 'M', 20),
        ('l', 'L', 30),
        ('xl', 'XL', 40),
        ('xxl', 'XXL', 50),
    ]
    for slug, label, so in rows:
        conn.execute(
            sa.text(
                """
                INSERT INTO merch_sizes (slug, label, sort_order, created_at, updated_at)
                VALUES (:slug, :lbl, :so, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {'slug': slug, 'lbl': label, 'so': so},
        )


def _backfill(conn):
    _seed_default_sizes(conn)

    def max_sort(table: str) -> int:
        r = conn.scalar(
            sa.text(f'SELECT COALESCE(MAX(sort_order), 0) FROM {table}')
        )
        return int(r or 0)

    co_base = max_sort('merch_colors')
    sz_base = max_sort('merch_sizes')
    co_counter = {'v': co_base}
    sz_counter = {'v': sz_base}

    def next_co():
        co_counter['v'] += 1
        return co_counter['v']

    def next_sz():
        sz_counter['v'] += 1
        return sz_counter['v']

    def get_or_make_color(label: str) -> int:
        base_slug = _slugify_ascii_label(label)
        slug_try = base_slug
        suffix = 2
        lbl = label[:160]
        while True:
            rid = conn.scalar(
                sa.text('SELECT id FROM merch_colors WHERE slug = :slug'),
                {'slug': slug_try},
            )
            if rid is not None:
                return int(rid)
            try:
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO merch_colors
                        (slug, label, sort_order, created_at, updated_at)
                        VALUES (:slug, :lbl, :so, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """
                    ),
                    {
                        'slug': slug_try,
                        'lbl': lbl,
                        'so': next_co(),
                    },
                )
                nid = conn.scalar(
                    sa.text('SELECT id FROM merch_colors WHERE slug = :slug'),
                    {'slug': slug_try},
                )
                return int(nid)
            except IntegrityError:
                slug_try = f'{base_slug}-{suffix}'
                suffix += 1

    def get_or_make_size(label: str) -> int:
        slug = _slugify_ascii_label(label)
        rid = conn.scalar(
            sa.text('SELECT id FROM merch_sizes WHERE slug = :slug'),
            {'slug': slug},
        )
        if rid is not None:
            return int(rid)
        conn.execute(
            sa.text(
                """
                INSERT INTO merch_sizes
                (slug, label, sort_order, created_at, updated_at)
                VALUES (:slug, :lbl, :so, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {
                'slug': slug,
                'lbl': label[:160],
                'so': next_sz(),
            },
        )
        nid = conn.scalar(
            sa.text('SELECT id FROM merch_sizes WHERE slug = :slug'),
            {'slug': slug},
        )
        return int(nid)

    rows = conn.execute(
        sa.text('SELECT id, attributes FROM merch_variants ORDER BY id ASC')
    ).fetchall()
    for vid, attrs_col in rows:
        attrs = _attrs_dict(attrs_col)
        c_lbl = _pick_dimension(attrs, _COLOR_KEYS_CF)
        s_lbl = _pick_dimension(attrs, _SIZE_KEYS_CF)
        cid = get_or_make_color(c_lbl) if c_lbl else None
        sid = get_or_make_size(s_lbl) if s_lbl else None
        vk = _compute_variant_key_migration(cid, sid, attrs)
        conn.execute(
            sa.text(
                'UPDATE merch_variants SET color_id=:c, size_id=:s, variant_key=:vk '
                'WHERE id=:id'
            ),
            {'c': cid, 's': sid, 'vk': vk[:126], 'id': int(vid)},
        )
    _finalize_unique_variant_keys(conn)


def upgrade():
    op.create_table(
        'merch_colors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('label', sa.String(length=160), nullable=False),
        sa.Column(
            'sort_order',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_merch_colors_slug'),
    )
    op.create_index(
        'ix_nv2_merch_colors_slug', 'merch_colors', ['slug'], unique=False
    )

    op.create_table(
        'merch_sizes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('label', sa.String(length=160), nullable=False),
        sa.Column(
            'sort_order',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_merch_sizes_slug'),
    )
    op.create_index(
        'ix_nv2_merch_sizes_slug', 'merch_sizes', ['slug'], unique=False
    )

    with op.batch_alter_table('merch_variants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('color_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('size_id', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('variant_key', sa.String(length=128), nullable=True)
        )

    bind = op.get_bind()
    _backfill(bind)
    bind.commit()

    with op.batch_alter_table('merch_variants', schema=None) as batch_op:
        batch_op.alter_column(
            'variant_key',
            existing_type=sa.String(length=128),
            nullable=False,
        )
        batch_op.create_foreign_key(
            'fk_nv2_merch_variants_color_id',
            'merch_colors',
            ['color_id'],
            ['id'],
            ondelete='RESTRICT',
        )
        batch_op.create_foreign_key(
            'fk_nv2_merch_variants_size_id',
            'merch_sizes',
            ['size_id'],
            ['id'],
            ondelete='RESTRICT',
        )
        batch_op.create_unique_constraint(
            'uq_nv2_merch_variants_article_variant_key',
            ['article_id', 'variant_key'],
        )


def downgrade():
    with op.batch_alter_table('merch_variants', schema=None) as batch_op:
        batch_op.drop_constraint(
            'uq_nv2_merch_variants_article_variant_key', type_='unique'
        )
        batch_op.drop_constraint(
            'fk_nv2_merch_variants_size_id', type_='foreignkey'
        )
        batch_op.drop_constraint(
            'fk_nv2_merch_variants_color_id', type_='foreignkey'
        )
        batch_op.drop_column('variant_key')
        batch_op.drop_column('size_id')
        batch_op.drop_column('color_id')

    op.drop_index('ix_nv2_merch_sizes_slug', table_name='merch_sizes')
    op.drop_table('merch_sizes')

    op.drop_index('ix_nv2_merch_colors_slug', table_name='merch_colors')
    op.drop_table('merch_colors')
