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
    rv = logged_in_client.get('/admin/merch-v2/', follow_redirects=True)
    assert rv.status_code == 403


def test_cockpit_marketingchef_ok(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.get('/admin/merch-v2/', follow_redirects=True)
    assert rv.status_code == 200


def test_cockpit_redirects_canonical_tab(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.get('/admin/merch-v2/', follow_redirects=False)
    assert rv.status_code == 302
    loc = rv.headers.get('Location', '')
    assert 'tab=cockpit' in loc
    assert 'panel=' not in loc


def test_cockpit_invalid_tab_redirects(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.get('/admin/merch-v2/?tab=invalid', follow_redirects=False)
    assert rv.status_code == 302
    loc = rv.headers.get('Location', '')
    assert 'tab=cockpit' in loc
    assert 'panel=' not in loc


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
            'submit': 'Variante hinzufügen',
        },
        follow_redirects=False,
    )
    assert rv_item.status_code == 302

    with app.app_context():
        from backend.models.merch_v2 import MerchRoundItem

        assert MerchRoundItem.query.filter_by(round_id=rid, variant_id=vid).count() == 1

    rv2 = marketing_chief_client.post(f'/admin/merch-v2/rounds/{rid}/open', follow_redirects=True)
    assert rv2.status_code == 200
    assert 'Bestellungen sammeln'.encode('utf-8') in rv2.data

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
        data={'variant_id': vid, 'submit': 'Variante hinzufügen'},
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


def test_round_add_all_items(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchSupplier, MerchVariant

        s = MerchSupplier(name='AddAll-Lief')
        db.session.add(s)
        db.session.flush()
        art1 = MerchArticle(name='Hoodie', supplier_id=s.id, list_price_rappen=5000)
        art2 = MerchArticle(name='Cap', supplier_id=s.id, list_price_rappen=1500)
        db.session.add_all([art1, art2])
        db.session.flush()
        v1 = MerchVariant(article_id=art1.id, attributes={}, is_active=True)
        v2 = MerchVariant(article_id=art2.id, attributes={}, is_active=True)
        db.session.add_all([v1, v2])
        db.session.commit()

    marketing_chief_client.post(
        '/admin/merch-v2/rounds',
        data={'title': 'AddAll-R', 'subsidy_chf': '0', 'submit': 'Runde speichern'},
        follow_redirects=True,
    )
    with app.app_context():
        from backend.models.merch_v2 import MerchRound, MerchRoundItem

        rid = MerchRound.query.filter_by(title='AddAll-R').first().id
        assert MerchRoundItem.query.filter_by(round_id=rid).count() == 0

    rv = marketing_chief_client.post(
        f'/admin/merch-v2/rounds/{rid}/items/add-all',
        follow_redirects=False,
    )
    assert rv.status_code == 302

    with app.app_context():
        from backend.models.merch_v2 import MerchRoundItem

        assert MerchRoundItem.query.filter_by(round_id=rid).count() == 2


def test_round_step_back_from_open(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchRound, MerchSupplier, MerchVariant

        s = MerchSupplier(name='Back-Lief')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Back-Art', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()
        vid = v.id
        db.session.commit()

    marketing_chief_client.post(
        '/admin/merch-v2/rounds',
        data={'title': 'Back-R', 'subsidy_chf': '0', 'submit': 'Runde speichern'},
        follow_redirects=True,
    )
    with app.app_context():
        rid = MerchRound.query.filter_by(title='Back-R').first().id

    marketing_chief_client.post(
        f'/admin/merch-v2/rounds/{rid}/items',
        data={'variant_id': vid, 'submit': 'Variante hinzufügen'},
        follow_redirects=True,
    )
    marketing_chief_client.post(f'/admin/merch-v2/rounds/{rid}/open', follow_redirects=True)

    rv = marketing_chief_client.post(
        f'/admin/merch-v2/rounds/{rid}/step-back',
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert 'Schritt zurück'.encode('utf-8') in rv.data

    with app.app_context():
        r = db.session.get(MerchRound, rid)
        assert r.status.value == 'DRAFT'


def test_round_delete_draft(marketing_chief_client, app, merch_v2_enabled):
    marketing_chief_client.post(
        '/admin/merch-v2/rounds',
        data={'title': 'Del-R', 'subsidy_chf': '0', 'submit': 'Runde speichern'},
        follow_redirects=True,
    )
    with app.app_context():
        from backend.models.merch_v2 import MerchRound

        rid = MerchRound.query.filter_by(title='Del-R').first().id

    rv = marketing_chief_client.post(
        f'/admin/merch-v2/rounds/{rid}/delete',
        follow_redirects=True,
    )
    assert rv.status_code == 200

    with app.app_context():
        from backend.models.merch_v2 import MerchRound

        assert MerchRound.query.filter_by(id=rid).first() is None


def test_open_round_shows_bestellrunde_schliessen(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchRound, MerchSupplier, MerchVariant

        s = MerchSupplier(name='Ui-Lief')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Ui-Art', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()
        vid = v.id
        db.session.commit()

    marketing_chief_client.post(
        '/admin/merch-v2/rounds',
        data={'title': 'Ui-R', 'subsidy_chf': '0', 'submit': 'Runde speichern'},
        follow_redirects=True,
    )
    with app.app_context():
        rid = MerchRound.query.filter_by(title='Ui-R').first().id

    marketing_chief_client.post(
        f'/admin/merch-v2/rounds/{rid}/items',
        data={'variant_id': vid, 'submit': 'Variante hinzufügen'},
        follow_redirects=True,
    )
    marketing_chief_client.post(f'/admin/merch-v2/rounds/{rid}/open', follow_redirects=True)

    rv = marketing_chief_client.get(f'/admin/merch-v2/rounds/{rid}')
    assert rv.status_code == 200
    assert b'Bestellrunde schliessen' in rv.data
    assert b'merch-round-orders-section' in rv.data


def test_suppliers_index_ok(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.get('/admin/merch-v2/suppliers', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Lieferanten' in rv.data


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
    rv = marketing_chief_client.get('/admin/merch-v2/articles', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Sortiment' in rv.data


def test_article_create_variants(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchColor, MerchSupplier

        sup = MerchSupplier(name='Art-Lief')
        c_marine = MerchColor(slug='marine', label='marine', sort_order=1)
        c_schwarz = MerchColor(slug='schwarz', label='schwarz', sort_order=2)
        db.session.add_all([sup, c_marine, c_schwarz])
        db.session.commit()
        sid = sup.id
        cid_marine, cid_schwarz = c_marine.id, c_schwarz.id

    rv = marketing_chief_client.post(
        '/admin/merch-v2/articles/new',
        data={
            'name': 'Test-Polo',
            'supplier_id': sid,
            'description': 'd',
            'list_price_chf': '39.90',
            'color_choice_ids': [str(cid_marine), str(cid_schwarz)],
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
        from backend.models.merch_v2 import MerchArticle, MerchColor, MerchSupplier, MerchVariant

        mc_rot = MerchColor(slug='rot', label='rot', sort_order=1)
        mc_blau = MerchColor(slug='blau', label='blau', sort_order=2)
        db.session.add_all([mc_rot, mc_blau])
        db.session.flush()

        sup = MerchSupplier(name='Price-Lief')
        db.session.add(sup)
        db.session.flush()
        sid = sup.id
        cid_rot, cid_blau = mc_rot.id, mc_blau.id
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
            'remove_image': False,
            'color_choice_ids': [str(cid_rot), str(cid_blau)],
            f'variant_list_price_chf_{vid1}': '34.50',
            'submit': 'Speichern',
        },
    )
    with app.app_context():
        v1b = db.session.get(MerchVariant, vid1)
        assert v1b.list_price_rappen == 3450
        v2b = MerchVariant.query.filter_by(article_id=aid, attributes={'farbe': 'blau'}).first()
        assert v2b.list_price_rappen is None


def test_merch_lookups_hub_ok(marketing_chief_client, merch_v2_enabled):
    rv = marketing_chief_client.get('/admin/merch-v2/lookups', follow_redirects=False)
    assert rv.status_code == 302
    assert '/lookups/colors' in (rv.headers.get('Location') or '')
    rv2 = marketing_chief_client.get('/admin/merch-v2/lookups/colors')
    assert rv2.status_code == 200
    assert 'Farben' in rv2.get_data(as_text=True)


def test_merch_lookup_color_create(marketing_chief_client, app, merch_v2_enabled):
    marketing_chief_client.post(
        '/admin/merch-v2/lookups/colors/new',
        data={'label': '  Testfarbe  '},
        follow_redirects=True,
    )
    with app.app_context():
        from backend.models.merch_v2 import MerchColor

        row = MerchColor.query.filter_by(slug='testfarbe').first()
        assert row is not None
        assert row.label == 'Testfarbe'


def test_merch_lookup_colors_bulk_save(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchColor

        c1 = MerchColor(slug='rot-save', label='rot', sort_order=1)
        c2 = MerchColor(slug='blau-save', label='blau', sort_order=2)
        db.session.add_all([c1, c2])
        db.session.commit()
        id1, id2 = c1.id, c2.id

    rv = marketing_chief_client.post(
        '/admin/merch-v2/lookups/colors/save',
        data={
            f'label_{id1}': 'Rot neu',
            f'label_{id2}': 'Blau neu',
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b'Farben gespeichert' in rv.data

    with app.app_context():
        from backend.models.merch_v2 import MerchColor

        assert MerchColor.query.filter_by(id=id1).first().label == 'Rot neu'
        assert MerchColor.query.filter_by(id=id2).first().label == 'Blau neu'


def test_article_bulk_deactivate_color(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchColor, MerchSupplier, MerchVariant

        col = MerchColor(slug='marine-tests', label='Marine Tests', sort_order=10)
        sup = MerchSupplier(name='Bulk-Lief')
        db.session.add_all([col, sup])
        db.session.flush()
        cid, sid = col.id, sup.id
        art = MerchArticle(name='Bulk-Polo', supplier_id=sid, list_price_rappen=3900)
        db.session.add(art)
        db.session.flush()
        pv = MerchVariant(
            article_id=art.id,
            color_id=cid,
            variant_key=f'bulk-t-{cid}-a',
            attributes={'farbe': 'Marine'},
            is_active=True,
        )
        db.session.add(pv)
        db.session.flush()
        vid, aid = pv.id, art.id
        db.session.commit()

    marketing_chief_client.post(
        f'/admin/merch-v2/articles/{aid}/variants/bulk-deactivate-color',
        data={'color_id': cid},
        follow_redirects=True,
    )
    with app.app_context():
        v = db.session.get(MerchVariant, vid)
        assert v.is_active is False


def test_article_new_stash_supplier_and_return(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchColor, MerchSupplier

        sup = MerchSupplier(name='Bestehend-Lief')
        col = MerchColor(slug='gruen-stash', label='gruen', sort_order=1)
        db.session.add_all([sup, col])
        db.session.commit()
        sid = sup.id
        cid = col.id

    rv = marketing_chief_client.post(
        '/admin/merch-v2/articles/new/stash-for-supplier',
        data={
            'name': 'Draft-Artikel',
            'supplier_id': sid,
            'description': 'Entwurfstext',
            'list_price_chf': '25.50',
            'color_choice_ids': [str(cid)],
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b'Neuer Lieferant' in rv.data
    assert b'Zur' in rv.data and b'ck zum Artikel' in rv.data

    rv = marketing_chief_client.post(
        '/admin/merch-v2/suppliers/new',
        data={
            'name': 'Frisch-Erfasst',
            'contact_email': '',
            'website_url': '',
            'notes': '',
            'submit': 'Speichern',
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b'Draft-Artikel' in rv.data
    assert b'Entwurfstext' in rv.data
    assert b'Frisch-Erfasst' in rv.data
    assert b'Lieferant erfassen' in rv.data


def test_article_edit_stash_supplier_cancel_restores_draft(marketing_chief_client, app, merch_v2_enabled):
    with app.app_context():
        from backend.models.merch_v2 import MerchArticle, MerchSupplier

        sup = MerchSupplier(name='Edit-Lief')
        db.session.add(sup)
        db.session.flush()
        art = MerchArticle(name='Original-Name', supplier_id=sup.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.commit()
        aid, sid = art.id, sup.id

    marketing_chief_client.post(
        f'/admin/merch-v2/articles/{aid}/stash-for-supplier',
        data={
            'name': 'Geaendert im Entwurf',
            'supplier_id': sid,
            'description': 'Neue Beschreibung',
            'list_price_chf': '12.00',
        },
        follow_redirects=True,
    )
    rv = marketing_chief_client.get(f'/admin/merch-v2/articles/{aid}/edit', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Geaendert im Entwurf' in rv.data
    assert b'Neue Beschreibung' in rv.data
