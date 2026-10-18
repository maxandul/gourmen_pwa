"""Merch area grants, native roles and direct URL boundaries with synthetic data."""
from datetime import datetime
import pytest
from backend.extensions import db
from backend.models.member import Member, Funktion
from backend.models.merch_order import MerchOrder, OrderStatus
from backend.models.merch_article import MerchArticle
from backend.models.member_area_grant import MemberAreaGrant
from backend.services.area_permissions import AreaPermissionService
from tests.routes.test_event_visibility import visibility_data, login


@pytest.fixture
def merch_case(app,visibility_data):
    members,_=visibility_data
    with app.app_context():
        order=MerchOrder(member_id=members[0],order_number='PRIVATE-ORDER',status=OrderStatus.BESTELLT,
            total_member_price_rappen=100,total_supplier_price_rappen=90,total_profit_rappen=10)
        article=MerchArticle(name='Synthetic shirt',base_supplier_price_rappen=90,base_member_price_rappen=100)
        db.session.add_all([order,article]);db.session.commit()
        return members,order.id,article.id


@pytest.mark.parametrize('kind',['member','board','finance','travel','marketing','grant','admin'])
def test_merch_area_matrix(app,client,merch_case,kind):
    members,oid,aid=merch_case
    actor=members[3] if kind=='admin' else members[1]
    allowed=kind in ['marketing','grant','admin']
    with app.app_context():
        member=db.session.get(Member,actor)
        member.vorstandsmitglied=kind=='board'
        member.funktion={'marketing':Funktion.MARKETINGCHEF,'finance':Funktion.SCHATZMEISTER,
            'travel':Funktion.REISEKOMMISSAR}.get(kind,Funktion.MEMBER)
        if kind=='grant':db.session.add(MemberAreaGrant(member_id=actor,scope='merch_manage',granted_by=members[3]))
        db.session.commit()
    login(client,actor)
    for path in ['/admin/merch','/admin/merch?tab=supplier','/admin/merch?tab=articles',
                 f'/admin/merch/orders/{oid}',f'/admin/merch/articles/{aid}',
                 '/admin/merch/articles/new',f'/admin/merch/articles/{aid}/edit']:
        assert client.get(path).status_code==(200 if allowed else 403)
    assert ('/admin/merch' in client.get('/member/').get_data(as_text=True))==allowed
    for suffix in ['status','status-update']:
        assert client.post(f'/admin/merch/orders/{oid}/{suffix}',data={'status':'BESTELLT'}).status_code==(302 if allowed else 403)
    data={'name':'New synthetic shirt','base_supplier_price_chf':'2','base_member_price_chf':'1',
          'colors':'blue','sizes':'M','is_active':'on'}
    assert client.post('/admin/merch/articles/new',data=data).status_code==(302 if allowed else 403)
    assert client.post(f'/admin/merch/articles/{aid}/edit',data=data).status_code==(302 if allowed else 403)
    with app.app_context():
        assert MerchArticle.query.count()==(2 if allowed else 1)
        assert db.session.get(MerchArticle,aid).name==('New synthetic shirt' if allowed else 'Synthetic shirt')
    # Even managers do not impersonate an owner through the member endpoint.
    assert client.get(f'/member/merch/order/{oid}/edit').status_code==404
    assert client.get('/member/merch').status_code==200
    if kind!='admin':
        assert client.post(f'/admin/members/{members[0]}/area-permissions').status_code==403


def test_revocation_and_own_orders(app,client,merch_case):
    members,oid,_=merch_case
    with app.app_context():
        db.session.add(MemberAreaGrant(member_id=members[0],scope='merch_manage',granted_by=members[3]))
        db.session.commit()
    login(client,members[0]);assert client.get('/admin/merch').status_code==200
    with app.app_context():
        actor=db.session.get(Member,members[0]);actor.is_active=False
        assert not AreaPermissionService.has_scope(actor,'merch_manage')
        actor.is_active=True
        MemberAreaGrant.query.one().revoked_at=datetime.now();db.session.commit()
    assert client.get('/admin/merch').status_code==403
    assert client.get(f'/member/merch/order/{oid}').status_code==302
    assert f'/member/merch/order/{oid}/edit' in client.get('/member/merch?tab=orders').get_data(as_text=True)
