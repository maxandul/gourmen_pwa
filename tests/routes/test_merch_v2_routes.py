"""Merch v2: Shop-Landing und Admin-Cockpit (Feature-Flag, Permissions)."""

from __future__ import annotations

import pytest
from werkzeug.security import generate_password_hash

import backend.models  # noqa: F401
from backend.extensions import db
from backend.models.member import Funktion, Member


@pytest.fixture
def merch_v2_enabled(app, monkeypatch):
    monkeypatch.setitem(app.config, 'MERCH_V2_ENABLED', True)


@pytest.fixture
def marketing_chief_member_id(app):
    with app.app_context():
        m = Member(
            vorname='M',
            nachname='Chef',
            email='mc-merch-v2@example.test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
            funktion=Funktion.MARKETINGCHEF,
        )
        db.session.add(m)
        db.session.commit()
        return m.id


@pytest.fixture
def marketing_chief_client(app, client, marketing_chief_member_id):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(marketing_chief_member_id)
        sess['_fresh'] = True
    return client


def test_shop_anonymous_redirects(client, app, merch_v2_enabled):
    rv = client.get('/merch/')
    assert rv.status_code == 302


def test_shop_feature_off_404(logged_in_client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'MERCH_V2_ENABLED', False)
    rv = logged_in_client.get('/merch/')
    assert rv.status_code == 404


def test_shop_ok(logged_in_client, app, merch_v2_enabled):
    rv = logged_in_client.get('/merch/')
    assert rv.status_code == 200
    assert b'Merch' in rv.data


def test_cockpit_member_forbidden(logged_in_client, app, merch_v2_enabled):
    rv = logged_in_client.get('/admin/merch-v2/')
    assert rv.status_code == 403


def test_cockpit_marketingchef_ok(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.get('/admin/merch-v2/')
    assert rv.status_code == 200


def test_round_new_schatzmeister_forbidden(app, client, merch_v2_enabled):
    with app.app_context():
        m = Member(
            vorname='S',
            nachname='Treasurer',
            email='treasurer-merch-v2@example.test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
            funktion=Funktion.SCHATZMEISTER,
        )
        db.session.add(m)
        db.session.commit()
        uid = m.id
    with client.session_transaction() as sess:
        sess['_user_id'] = str(uid)
        sess['_fresh'] = True
    rv = client.get('/admin/merch-v2/rounds/new')
    assert rv.status_code == 403


def test_round_create_and_open(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchSupplier, MerchVariant

        s = MerchSupplier(name='Merch-Test-Lief')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Winter-Cap', supplier_id=s.id, list_price_rappen=1800)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={'farbe': 'marine'}, is_active=True)
        db.session.add(v)
        db.session.flush()
        vid = v.id
        db.session.commit()

    rv = marketing_chief_client.post(
        '/admin/merch-v2/rounds',
        data={
            'title': 'Winter 2026',
            'description': 'Kapellen',
            'subsidy_chf': '12.50',
            'submit': 'Runde speichern',
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert '/admin/merch-v2/rounds/' in rv.headers.get('Location', '')

    with app.app_context():
        from backend.models.merch_v2 import MerchRound

        r = MerchRound.query.filter_by(title='Winter 2026').first()
        assert r is not None
        assert r.status.value == 'DRAFT'
        assert r.subsidy_per_member_rappen == 1250
        rid = r.id

    rv_item = marketing_chief_client.post(
        f'/admin/merch-v2/rounds/{rid}/items',
        data={
            'variant_id': vid,
            'submit': 'Position hinzufuegen',
        },
        follow_redirects=False,
    )
    assert rv_item.status_code == 302

    with app.app_context():
        from backend.models.merch_v2 import MerchRoundItem

        assert MerchRoundItem.query.filter_by(round_id=rid, variant_id=vid).count() == 1

    rv2 = marketing_chief_client.post(f'/admin/merch-v2/rounds/{rid}/open', follow_redirects=True)
    assert rv2.status_code == 200
    assert b'OPEN' in rv2.data

    with app.app_context():
        from backend.models.merch_v2 import MerchRound

        r2 = db.session.get(MerchRound, rid)
        assert r2.status.value == 'OPEN'
        assert r2.opened_at is not None


def test_round_open_blocked_without_items(marketing_chief_client, app, merch_v2_enabled):
    marketing_chief_client.post(
        '/admin/merch-v2/rounds',
        data={
            'title': 'Leer-Runde',
            'subsidy_chf': '0',
            'submit': 'Runde speichern',
        },
        follow_redirects=True,
    )
    with app.app_context():
        from backend.models.merch_v2 import MerchRound

        rid = MerchRound.query.filter_by(title='Leer-Runde').first().id

    rv = marketing_chief_client.post(f'/admin/merch-v2/rounds/{rid}/open', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Sortimentsposition' in rv.data

    with app.app_context():
        from backend.models.merch_v2 import MerchRound

        assert db.session.get(MerchRound, rid).status.value == 'DRAFT'


def test_round_shop_cart_confirm(logged_in_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.member import Member
        from backend.models.merch_v2 import (
            MerchArticle,
            MerchRound,
            MerchRoundItem,
            MerchRoundStatus,
            MerchSupplier,
            MerchVariant,
        )
        from backend.services.merch_round_service import MerchRoundService

        uid = Member.query.filter_by(email='docs-smoke@example.test').one().id

        s = MerchSupplier(name='ShopSeed-Lief')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='ShopSeed-Art', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(
            title='ShopSeed-Runde',
            marketing_chief_id=uid,
            subsidy_per_member_rappen=500,
        )
        db.session.commit()
        rid = cr['round'].id
        MerchRoundService.add_variant_to_round(rid, v.id)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)
        MerchRoundService.apply_transition(rnd, MerchRoundStatus.OPEN)
        db.session.commit()

        ri = MerchRoundItem.query.filter_by(round_id=rid).one()
        riid = ri.id

    rv = logged_in_client.get(f'/merch/rounds/{rid}')
    assert rv.status_code == 200

    logged_in_client.post(
        f'/merch/rounds/{rid}/cart',
        data={'round_item_id': riid, 'quantity': 2},
    )

    with app.app_context():
        from backend.models.merch_v2 import MerchOrder

        o = MerchOrder.query.filter_by(round_id=rid, member_id=uid).one()
        assert o.status.value == 'DRAFT'
        assert o.gross_amount_rappen == 2000
        assert o.subsidy_amount_rappen == 500
        assert o.member_amount_due_rappen == 1500
        oid = o.id

    logged_in_client.post(f'/merch/rounds/{rid}/confirm', data={})

    with app.app_context():
        from backend.models.merch_v2 import MerchOrder

        o2 = db.session.get(MerchOrder, oid)
        assert o2.status.value == 'CONFIRMED'
        assert o2.confirmed_at is not None


def test_round_remove_item(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchRoundItem, MerchSupplier, MerchVariant

        s = MerchSupplier(name='RItem-Lief')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Polo', supplier_id=s.id, list_price_rappen=4000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()
        vid = v.id
        db.session.commit()

    marketing_chief_client.post(
        '/admin/merch-v2/rounds',
        data={'title': 'R-T', 'subsidy_chf': '0', 'submit': 'Runde speichern'},
        follow_redirects=True,
    )
    with app.app_context():
        from backend.models.merch_v2 import MerchRound

        rid = MerchRound.query.filter_by(title='R-T').first().id

    marketing_chief_client.post(
        f'/admin/merch-v2/rounds/{rid}/items',
        data={'variant_id': vid, 'submit': 'Position hinzufuegen'},
        follow_redirects=True,
    )

    with app.app_context():
        item = MerchRoundItem.query.filter_by(round_id=rid).first()
        iid = item.id

    marketing_chief_client.post(
        f'/admin/merch-v2/rounds/{rid}/items/{iid}/remove',
        follow_redirects=True,
    )

    with app.app_context():
        assert MerchRoundItem.query.filter_by(round_id=rid).count() == 0


def test_suppliers_index_ok(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.get('/admin/merch-v2/suppliers')
    assert rv.status_code == 200


def test_supplier_create_redirects(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.post(
        '/admin/merch-v2/suppliers/new',
        data={
            'name': 'ACME Caps',
            'contact_email': 'x@example.test',
            'website_url': '',
            'notes': 'n',
            'submit': 'Speichern',
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302


def test_supplier_archive_blocked_with_active_article(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchSupplier

        sup = MerchSupplier(name='S-arch-block')
        db.session.add(sup)
        db.session.flush()
        db.session.add(
            MerchArticle(name='Keeps-supplier', supplier_id=sup.id, list_price_rappen=100),
        )
        sid = sup.id
        db.session.commit()

    rv = marketing_chief_client.post(f'/admin/merch-v2/suppliers/{sid}/archive', follow_redirects=True)
    assert rv.status_code == 200
    assert b'aktive Artikel' in rv.data

    with app.app_context():
        from backend.models.merch_v2 import MerchSupplier

        assert MerchSupplier.query.filter_by(id=sid).first().is_archived is False


def test_articles_index_ok(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.get('/admin/merch-v2/articles')
    assert rv.status_code == 200


def test_article_create_variants(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchSupplier

        sup = MerchSupplier(name='Art-Lief')
        db.session.add(sup)
        db.session.commit()
        sid = sup.id

    rv = marketing_chief_client.post(
        '/admin/merch-v2/articles/new',
        data={
            'name': 'Test-Polo',
            'supplier_id': sid,
            'description': 'd',
            'list_price_chf': '39.90',
            'variant_schema_text': 'farbe: marine, schwarz',
            'submit': 'Speichern',
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert '/admin/merch-v2/articles/' in rv.headers.get('Location', '')
    assert '/edit' in rv.headers.get('Location', '')

    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchVariant

        art = MerchArticle.query.filter_by(name='Test-Polo').first()
        assert art is not None
        assert art.list_price_rappen == 3990
        assert MerchVariant.query.filter_by(article_id=art.id, is_active=True).count() == 2


def test_article_variant_list_price_override(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchSupplier, MerchVariant

        sup = MerchSupplier(name='Price-Lief')
        db.session.add(sup)
        db.session.flush()
        sid = sup.id
        art = MerchArticle(name='Polo-Preis', supplier_id=sid, list_price_rappen=3000)
        db.session.add(art)
        db.session.flush()
        v1 = MerchVariant(article_id=art.id, attributes={'farbe': 'rot'}, is_active=True)
        v2 = MerchVariant(article_id=art.id, attributes={'farbe': 'blau'}, is_active=True)
        db.session.add_all([v1, v2])
        db.session.flush()
        vid1, aid = v1.id, art.id
        db.session.commit()

    marketing_chief_client.post(
        f'/admin/merch-v2/articles/{aid}/edit',
        data={
            'name': 'Polo-Preis',
            'supplier_id': sid,
            'description': '',
            'list_price_chf': '30.00',
            'variant_schema_text': 'farbe: rot, blau',
            'remove_image': False,
            f'variant_list_price_chf_{vid1}': '34.50',
            'submit': 'Speichern',
        },
    )
    with app.app_context():
        v1b = db.session.get(MerchVariant, vid1)
        assert v1b.list_price_rappen == 3450
        v2b = MerchVariant.query.filter_by(article_id=aid, attributes={'farbe': 'blau'}).first()
        assert v2b.list_price_rappen is None
