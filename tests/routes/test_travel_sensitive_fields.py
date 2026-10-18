"""R13 field projection and role/step-up checks with synthetic encrypted data."""
import time
import pytest
from cryptography.fernet import Fernet
from backend.extensions import db
from backend.models.member import Member, Funktion
from backend.models.member_sensitive import MemberSensitive
from backend.services.security import SecurityService
from tests.routes.test_event_visibility import visibility_data, login
from tests.conftest import auth_id


@pytest.fixture
def travel_data(app,visibility_data):
    members,_=visibility_data
    app.config['CRYPTO_KEY']=Fernet.generate_key().decode()
    with app.app_context():
        payload={'pass_nummer':'SYNTHETIC-PASS','id_nummer':'SYNTHETIC-ID',
                 'allergien':'HIDDEN-ALLERGY','unknown':'HIDDEN-EXTRA','fuehrerschein':'HIDDEN-LICENCE'}
        db.session.add(MemberSensitive(member_id=members[0],payload_encrypted=SecurityService.encrypt_json(payload)))
        db.session.get(Member,members[1]).funktion=Funktion.REISEKOMMISSAR
        db.session.commit()
    return members


def stepup(client,mid):
    login(client,mid)
    with client.session_transaction() as state:
        state['sensitive_access_until']=int(time.time())+600
        state['sensitive_access_member_id']=auth_id(client,mid)


@pytest.mark.parametrize('actor',[1,3])
def test_travel_view_projects_only_allowed_fields(app,client,travel_data,actor):
    members=travel_data;stepup(client,members[actor])
    response=client.get(f'/admin/members/{members[0]}/travel-documents');assert response.status_code==200
    body=response.get_data(as_text=True)
    assert 'SYNTHETIC-PASS' in body and 'SYNTHETIC-ID' in body
    for hidden in ['HIDDEN-ALLERGY','HIDDEN-EXTRA','HIDDEN-LICENCE']:
        assert hidden not in body
    assert 'no-store' in response.headers['Cache-Control']
    assert response.headers['Referrer-Policy']=='no-referrer'
    assert f'/admin/members/{members[0]}/travel-documents' in client.get('/admin/members').get_data(as_text=True)


@pytest.mark.parametrize('funktion',[f for f in Funktion if f != Funktion.REISEKOMMISSAR])
def test_other_roles_cannot_read_with_stepup(app,client,travel_data,monkeypatch,funktion):
    members=travel_data
    with app.app_context():
        actor=db.session.get(Member,members[2]);actor.funktion=funktion;db.session.commit()
    stepup(client,members[2])
    monkeypatch.setattr(SecurityService,'read_member_sensitive',lambda *_:pytest.fail('Unauthorized decrypt'))
    assert client.get(f'/admin/members/{members[0]}/travel-documents').status_code==403


@pytest.mark.parametrize('state',['missing','expired','foreign'])
def test_travel_requires_bound_stepup(app,client,travel_data,monkeypatch,state):
    members=travel_data;stepup(client,members[1])
    with client.session_transaction() as session:
        if state=='missing':session.pop('sensitive_access_until')
        elif state=='expired':session['sensitive_access_until']=0
        else:session['sensitive_access_member_id']=auth_id(client,members[3])
    monkeypatch.setattr(SecurityService,'read_member_sensitive',lambda *_:pytest.fail('Unconfirmed decrypt'))
    response=client.get(f'/admin/members/{members[0]}/travel-documents')
    assert response.status_code==302 and '/auth/step-up' in response.location
    assert 'no-store' in response.headers['Cache-Control']


def test_travel_cannot_write_or_open_full_admin_form(app,client,travel_data):
    members=travel_data;stepup(client,members[1])
    assert client.post(f'/admin/members/{members[0]}/travel-documents',data={'allergien':'changed'}).status_code==405
    assert client.get(f'/admin/members/{members[0]}/sensitive').status_code==403
    with app.app_context():
        sensitive=MemberSensitive.query.filter_by(member_id=members[0]).one()
        assert SecurityService.decrypt_json(sensitive.payload_encrypted)['allergien']=='HIDDEN-ALLERGY'


def test_travel_read_failure_preserves_payload(app,client,travel_data):
    members=travel_data;stepup(client,members[1])
    with app.app_context():
        sensitive=MemberSensitive.query.one();sensitive.payload_encrypted='synthetic-broken';db.session.commit()
    response=client.get(f'/admin/members/{members[0]}/travel-documents');assert response.status_code==500
    assert 'synthetic-broken' not in response.get_data(as_text=True)
    assert 'no-store' in response.headers['Cache-Control']
    with app.app_context():assert MemberSensitive.query.one().payload_encrypted=='synthetic-broken'
