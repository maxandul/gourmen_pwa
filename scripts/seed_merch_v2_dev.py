#!/usr/bin/env python3
"""
Merch v2 Demo-Daten fuer lokale Dev-DB (manuelle Tests im Browser).

Voraussetzungen:
- Alembic-Migrationen mit merch_* Tabellen angewendet
- Mindestens ein Mitglied (wird als marketing_chief_id der Runde gesetzt)

Optional:
- MERCH_V2_SEED_OWNER_EMAIL — Mitglied per E-Mail waehlen; sonst erstes Mitglied nach ID

Aufruf (PowerShell):

  $env:FLASK_ENV="development"; python scripts/seed_merch_v2_dev.py

Production nur nach Review; Script bricht ab, wenn die Demo-Runde schon existiert.
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.app import create_app  # noqa: E402
from backend.extensions import db  # noqa: E402
from backend.models.member import Member  # noqa: E402
from backend.models.merch_v2 import (  # noqa: E402
    MerchArticle,
    MerchRound,
    MerchRoundStatus,
    MerchSupplier,
    MerchVariant,
)
from backend.services.merch_round_service import MerchRoundService  # noqa: E402

ROUND_TITLE = 'Dev: Demo-Runde Merch v2'


def run() -> None:
    env_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env_name)

    with app.app_context():
        if not app.config.get('MERCH_V2_ENABLED'):
            print('Hinweis: MERCH_V2_ENABLED ist false — Daten sind nutzbar sobald das Flag gesetzt ist.')

        if MerchRound.query.filter_by(title=ROUND_TITLE).first():
            print(f'Abbruch: Runde "{ROUND_TITLE}" existiert bereits.')
            return

        owner_email = os.environ.get('MERCH_V2_SEED_OWNER_EMAIL')
        if owner_email:
            owner = Member.query.filter_by(email=owner_email).first()
            if not owner:
                print(f'Kein Mitglied mit E-Mail {owner_email!r}.')
                return
        else:
            owner = Member.query.order_by(Member.id).first()
            if not owner:
                print('Keine Mitglieder — bitte zuerst ein Mitglied anlegen.')
                return

        supplier = MerchSupplier(name='Demo Lieferant AG', contact_email='lieferant@example.test')
        db.session.add(supplier)
        db.session.flush()

        polo = MerchArticle(
            name='Demo Polo',
            description='Seed fuer Merch v2 (Dev)',
            supplier_id=supplier.id,
            list_price_rappen=4500,
            is_archived=False,
        )
        cap = MerchArticle(
            name='Demo Cap',
            description='Seed fuer Merch v2 (Dev)',
            supplier_id=supplier.id,
            list_price_rappen=2200,
            is_archived=False,
        )
        db.session.add_all([polo, cap])
        db.session.flush()

        v_polo_m = MerchVariant(
            article_id=polo.id,
            attributes={'farbe': 'marine', 'groesse': 'M'},
            is_active=True,
        )
        v_polo_l = MerchVariant(
            article_id=polo.id,
            attributes={'farbe': 'marine', 'groesse': 'L'},
            is_active=True,
        )
        v_cap = MerchVariant(article_id=cap.id, attributes={}, is_active=True)
        db.session.add_all([v_polo_m, v_polo_l, v_cap])
        db.session.flush()

        created = MerchRoundService.create_draft_round(
            title=ROUND_TITLE,
            marketing_chief_id=owner.id,
            description='Automatisch durch scripts/seed_merch_v2_dev.py',
            subsidy_per_member_rappen=1500,
        )
        if not created['success']:
            print(created.get('error', 'Runde fehlgeschlagen'))
            db.session.rollback()
            return
        db.session.commit()
        rnd = created['round']

        for vid in (v_polo_m.id, v_polo_l.id, v_cap.id):
            add_res = MerchRoundService.add_variant_to_round(rnd.id, vid)
            if not add_res['success']:
                print(add_res.get('error', 'Position fehlgeschlagen'))
                db.session.rollback()
                return
        db.session.commit()

        rnd_obj = db.session.get(MerchRound, rnd.id)
        open_res = MerchRoundService.apply_transition(rnd_obj, MerchRoundStatus.OPEN)
        if not open_res['success']:
            print(open_res.get('error', 'Oeffnen fehlgeschlagen'))
            db.session.rollback()
            return
        db.session.commit()

        print('OK Merch v2 Dev-Seed.')
        print(f'  Runden-ID: {rnd.id}')
        print(f'  Marketingchef-FK: Mitglied id={owner.id} ({owner.email})')
        print(f'  URLs: /merch/ — /merch/rounds/{rnd.id}')


if __name__ == '__main__':
    run()
