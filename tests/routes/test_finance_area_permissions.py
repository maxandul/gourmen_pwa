"""Finance scope enforcement with synthetic grants; no notification or Drive I/O."""
import pytest
from datetime import datetime
from backend.extensions import db
from backend.models.member import Member, Funktion
from backend.models.member_area_grant import MemberAreaGrant
from backend.services.area_permissions import AreaPermissionService
from tests.routes.test_upload_selection_permissions import selection_data
from tests.routes.test_event_visibility import visibility_data, login


@pytest.fixture
def finance_actor(app,selection_data):
    members,events,bookings,fy=selection_data
    def prepare(scope):
        with app.app_context():
            db.session.add(MemberAreaGrant(member_id=members[1],scope=scope,granted_by=members[3]))
            db.session.commit()
        return members,events,bookings,fy
    return prepare


@pytest.mark.parametrize('scope',['accounting_read','accounting_write'])
def test_finance_read_navigation_and_write_boundaries(app,client,finance_actor,scope):
    members,events,bookings,fy=finance_actor(scope);login(client,members[1])
    assert client.get('/accounting/').status_code==200
    detail=client.get(f'/accounting/booking/{bookings[0]}')
    assert detail.status_code==200
    assert ('/comment' in detail.get_data(as_text=True)) == (scope=='accounting_write')
    assert '/submit' not in client.get('/accounting/?tab=abschluss').get_data(as_text=True)
    assert client.get(f'/accounting/export/{fy}/csv').status_code==200
    assert '/accounting/' in client.get('/member/').get_data(as_text=True)
    assert client.get('/accounting/booking/new').status_code==(200 if scope=='accounting_write' else 403)
    assert client.get('/accounting/?tab=import').status_code==(200 if scope=='accounting_write' else 403)
    # Invalid form for permitted writer; reader must fail before form handling.
    response=client.post(f'/accounting/booking/{bookings[0]}/edit',data={})
    assert response.status_code==(400 if scope=='accounting_write' else 403)
    for action in ['submit','withdraw','approve','revoke']:
        assert client.post(f'/accounting/year/{fy}/{action}').status_code==403
    assert client.get(f'/admin/members/{members[0]}/sensitive').status_code==403
    assert client.post(f'/admin/members/{members[2]}/area-permissions').status_code==403


def test_finance_grant_revocation_and_inactive_account(app,client,finance_actor):
    members,_,_,_=finance_actor('accounting_write');login(client,members[1])
    with app.app_context():
        member=db.session.get(Member,members[1]);assert AreaPermissionService.has_scope(member,'accounting_read')
        member.is_active=False
        assert not AreaPermissionService.has_scope(member,'accounting_write')
        member.is_active=True
        MemberAreaGrant.query.one().revoked_at=datetime.now();db.session.commit()
    assert client.get('/accounting/').status_code==403


@pytest.mark.parametrize('function,write',[(Funktion.SCHATZMEISTER,True),(Funktion.RECHNUNGSPRUEFER,False)])
def test_native_finance_roles_remain(app,client,selection_data,function,write):
    members,_,_,_=selection_data
    with app.app_context():
        db.session.get(Member,members[1]).funktion=function;db.session.commit()
    login(client,members[1])
    assert client.get('/accounting/').status_code==200
    assert client.get('/accounting/?tab=kontenplan').status_code==(200 if write else 403)
