"""A-055: retained prices, no-op saves and conflict-safe original edit route."""
import json
import re
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
from backend.models.merch_order import MerchOrder
from backend.models.merch_order_item import MerchOrderItem
from backend.models.accounting import MemberClaim, ClaimType
from tests.routes.test_merch_read_only import catalogue
from tests.services.test_audit_failure_boundary import seed


def form(client,ids,quantity='1',color='HistoricalRed',size='XL',**changes):
    response=client.get(f'/member/merch/order/{ids[3]}/edit')
    assert response.status_code==200
    token=re.search(r'name="order_edit_version" value="([a-f0-9]+)"',response.text).group(1)
    data={f'color_{ids[0]}[]':[color],f'size_{ids[0]}[]':[size],f'quantity_{ids[0]}[]':[quantity],'order_edit_version':token}
    data.update(changes);return data


def post(client,ids,data):
    return client.post(f'/member/merch/order/{ids[3]}/edit',data=data)


def activate(app,ids):
    with app.app_context():
        db.session.get(MerchVariant,ids[2]).is_active=True;db.session.commit()


def test_noop_after_price_change_has_no_dml_and_preview_uses_bound_price(app,client,catalogue):
    with app.app_context():
        old=db.session.get(MerchVariant,catalogue[2]);old.member_price_rappen=9999;old.supplier_price_rappen=12000;db.session.commit();engine=db.engine
    response=client.get(f'/member/merch/order/{catalogue[3]}/edit')
    payload=json.loads(re.search(r'<script id="merch-order-edit-data" type="application/json">(.*?)</script>',response.text,re.S).group(1))
    saved=next(v for a in payload['articles'] for v in a['variants'] if v['id']==catalogue[2])
    assert saved['price']==1900
    data=form(client,catalogue)
    statements=[]
    def record(conn,cursor,sql,*args):statements.append(sql.lstrip().upper())
    sa_event.listen(engine,'before_cursor_execute',record)
    try:assert post(client,catalogue,data).status_code==302
    finally:sa_event.remove(engine,'before_cursor_execute',record)
    assert not any(sql.startswith(('INSERT','UPDATE','DELETE')) for sql in statements)
    with app.app_context():
        item=db.session.get(MerchOrderItem,catalogue[4]);assert item.variant_id==catalogue[2] and item.unit_member_price_rappen==1900
        assert item.description_snapshot is None and db.session.get(MerchOrder,catalogue[3]).total_member_price_rappen==1900


def test_quantity_edit_keeps_id_prices_and_description(app,client,catalogue):
    activate(app,catalogue)
    with app.app_context():
        item=db.session.get(MerchOrderItem,catalogue[4]);item.capture_description()
        variant=db.session.get(MerchVariant,catalogue[2]);variant.member_price_rappen=5000;variant.supplier_price_rappen=6000;db.session.commit()
    data=form(client,catalogue,quantity='3')
    assert post(client,catalogue,data).status_code==302
    with app.app_context():
        item=db.session.get(MerchOrderItem,catalogue[4]);assert item.quantity==3 and item.unit_member_price_rappen==1900 and item.total_member_price_rappen==5700
        assert item.description_snapshot=='Synthetic catalogue HistoricalRed XL'
        order=db.session.get(MerchOrder,catalogue[3]);assert (order.total_member_price_rappen,order.total_supplier_price_rappen,order.total_profit_rappen)==(5700,7500,-1800)
    assert post(client,catalogue,data).status_code==302  # Exact retry is a no-op despite old version.
    with app.app_context():assert MerchOrderItem.query.count()==1


def test_new_variant_does_not_reprice_retained_old_item(app,client,catalogue):
    data=form(client,catalogue)
    data.update({f'color_{catalogue[0]}[]':['HistoricalRed','ActiveBlue'],f'size_{catalogue[0]}[]':['XL','M'],f'quantity_{catalogue[0]}[]':['1','2']})
    assert post(client,catalogue,data).status_code==302
    with app.app_context():
        old=db.session.get(MerchOrderItem,catalogue[4]);assert old.quantity==1 and old.unit_member_price_rappen==1900
        new=MerchOrderItem.query.filter_by(variant_id=catalogue[1]).one();assert new.quantity==2 and new.unit_member_price_rappen==1500 and new.description_snapshot_source=='order'
        assert db.session.get(MerchOrder,catalogue[3]).total_member_price_rappen==4900


@pytest.mark.parametrize('change',['order','new_price'])
def test_stale_form_cannot_replace_newer_values(app,client,catalogue,change):
    activate(app,catalogue)
    data=form(client,catalogue,quantity='3')
    with app.app_context():
        if change=='order':
            item=db.session.get(MerchOrderItem,catalogue[4]);item.quantity=2;item.calculate_totals()
            order=db.session.get(MerchOrder,catalogue[3]);order.calculate_totals()
        else:db.session.get(MerchVariant,catalogue[1]).member_price_rappen=1600
        db.session.commit()
    response=post(client,catalogue,data)
    assert response.status_code==400 and 'inzwischen geändert' in response.text and 'value="3"' in response.text
    with app.app_context():assert db.session.get(MerchOrderItem,catalogue[4]).quantity==(2 if change=='order' else 1)


@pytest.mark.parametrize('paid',[0,500])
def test_existing_claim_blocks_change_but_allows_noop(app,client,catalogue,paid):
    activate(app,catalogue)
    with app.app_context():
        order=db.session.get(MerchOrder,catalogue[3]);claim=MemberClaim(member_id=order.member_id,merch_order_id=order.id,claim_type=ClaimType.MERCH,expected_rappen=1900,paid_rappen=paid)
        db.session.add(claim);db.session.commit()
    assert post(client,catalogue,form(client,catalogue)).status_code==302
    response=post(client,catalogue,form(client,catalogue,quantity='2'))
    assert response.status_code==400 and 'Forderung' in response.text
    with app.app_context():assert MemberClaim.query.one().paid_rappen==paid and db.session.get(MerchOrderItem,catalogue[4]).quantity==1


def test_inactive_own_variant_is_preserved_but_not_increased(app,client,catalogue):
    assert post(client,catalogue,form(client,catalogue)).status_code==302
    response=post(client,catalogue,form(client,catalogue,quantity='2'))
    assert response.status_code==400 and 'nicht erhöht' in response.text


@pytest.mark.parametrize('quantity',['-1','1.5','NaN','2147483648','2147483647','0'])
def test_invalid_or_empty_order_keeps_history(app,client,catalogue,quantity):
    activate(app,catalogue)
    assert post(client,catalogue,form(client,catalogue,quantity=quantity)).status_code==400
    with app.app_context():assert db.session.get(MerchOrderItem,catalogue[4]).quantity==1 and MerchOrderItem.query.count()==1


def test_mismatched_arrays_preserve_input_and_data(app,client,catalogue):
    data=form(client,catalogue);data[f'color_{catalogue[0]}[]'].append('Retain invalid input')
    response=post(client,catalogue,data)
    assert response.status_code==400 and 'Retain invalid input' in response.text
    with app.app_context():assert db.session.get(MerchOrderItem,catalogue[4]).quantity==1


def test_commit_failure_restores_position_and_totals(app,client,catalogue,monkeypatch):
    activate(app,catalogue);data=form(client,catalogue,quantity='2')
    def fail():raise OperationalError('synthetic',{},Exception('synthetic'))
    monkeypatch.setattr(db.session,'commit',fail)
    response=post(client,catalogue,data)
    assert response.status_code==400 and 'nicht gespeichert' in response.text
    with app.app_context():
        assert db.session.get(MerchOrderItem,catalogue[4]).quantity==1
        assert db.session.get(MerchOrder,catalogue[3]).total_member_price_rappen==1900


@pytest.mark.parametrize('inconsistent',['line','order'])
def test_inconsistent_old_totals_are_not_silently_repaired(app,client,catalogue,inconsistent):
    activate(app,catalogue)
    with app.app_context():
        target=db.session.get(MerchOrderItem,catalogue[4]) if inconsistent=='line' else db.session.get(MerchOrder,catalogue[3])
        target.total_member_price_rappen=1234;db.session.commit()
    response=post(client,catalogue,form(client,catalogue,quantity='2'))
    assert response.status_code==400 and 'widersprüchlich' in response.text
    with app.app_context():
        target=db.session.get(MerchOrderItem,catalogue[4]) if inconsistent=='line' else db.session.get(MerchOrder,catalogue[3])
        assert target.total_member_price_rappen==1234 and db.session.get(MerchOrderItem,catalogue[4]).quantity==1


def test_aggregate_quantity_limit_even_for_free_items(app,client,catalogue):
    activate(app,catalogue)
    with app.app_context():
        item=db.session.get(MerchOrderItem,catalogue[4]);item.unit_member_price_rappen=0;item.unit_supplier_price_rappen=0;item.calculate_totals()
        db.session.get(MerchOrder,catalogue[3]).calculate_totals();db.session.commit()
    data=form(client,catalogue)
    data.update({f'color_{catalogue[0]}[]':['HistoricalRed']*2,f'size_{catalogue[0]}[]':['XL']*2,f'quantity_{catalogue[0]}[]':['2147483647','1']})
    response=post(client,catalogue,data)
    assert response.status_code==400 and 'Gesamtmenge' in response.text
    with app.app_context():assert db.session.get(MerchOrderItem,catalogue[4]).quantity==1


def test_version_independent_of_relation_order(app, catalogue):
    from types import SimpleNamespace
    from backend.services.merch_order_edit import MerchOrderEditService
    with app.app_context():
        order = db.session.get(MerchOrder, catalogue[3])
        variant = db.session.get(MerchVariant, catalogue[1])
        variant.is_active = False
        item = MerchOrderItem(order_id=order.id, article_id=catalogue[0], variant_id=variant.id,
                              quantity=1, unit_member_price_rappen=1500, unit_supplier_price_rappen=2000)
        item.calculate_totals()
        db.session.add(item)
        db.session.commit()
        db.session.expire(order, ['order_items'])
        attrs = {key: getattr(order, key) for key in
                 ('id', 'status', 'total_member_price_rappen', 'total_supplier_price_rappen', 'total_profit_rappen')}
        forward = SimpleNamespace(**attrs, order_items=list(order.order_items))
        reverse = SimpleNamespace(**attrs, order_items=list(reversed(order.order_items)))
        assert MerchOrderEditService.context(forward)['order_edit_version'] == MerchOrderEditService.context(reverse)['order_edit_version']


def test_missing_color_preserves_other_posted_fields(app, client, catalogue):
    data = form(client, catalogue, quantity='7', size='Retain size')
    del data[f'color_{catalogue[0]}[]']
    response = post(client, catalogue, data)
    assert response.status_code == 400
    assert 'Retain size' in response.text and 'value="7"' in response.text
    with app.app_context():
        assert db.session.get(MerchOrderItem, catalogue[4]).quantity == 1
