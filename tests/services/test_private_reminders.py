"""Personal display is neither private payment proof nor a club booking."""
import re
from unittest.mock import Mock
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.accounting import MemberClaim,ClaimStatus,Booking
from backend.models.event import Event,EventAudience
from backend.models.member import Member,Role
from backend.services.accounting import AccountingService,AccountingValidationError
from backend.services.private_reminders import PrivateReminderService as Service
from backend.services.billbro_correction import record
from tests.services.test_billbro_correction import final_round,preview,confirm
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed
from tests.conftest import auth_id


@pytest.fixture
def private_round(app,client,final_round):
    with app.app_context(): payer=Member.query.filter(Member.id!=final_round[0]).first().id
    token=preview(client,final_round,dict(invoice='100',total='252',paid_by='mitglied',payer_member_id=str(payer),reason='Synthetic private'))
    assert confirm(client,final_round,token).status_code==302
    with app.app_context(): cid=MemberClaim.query.filter_by(member_id=final_round[0]).one().id
    return final_round[0],final_round[1],cid,payer


def token(app,ids):
    with app.app_context(): return Service.token(db.session.get(MemberClaim,ids[2]),db.session.get(Member,ids[0]))


def toggle(client,ids,tok,action='hide',return_to='dashboard'):
    return client.post(f'/member/private-reminders/{ids[2]}',data={'reminder_token':tok,'action':action,'return_to':return_to})


def finance(app):
    with app.app_context():
        return [dict((k,v) for k,v in record(c).items() if not k.startswith('private_reminder_')) for c in MemberClaim.query.order_by(MemberClaim.id)], [record(b) for b in Booking.query.all()]


def private_form(ids,**updates):
    values=dict(invoice='100',total='252',paid_by='mitglied',payer_member_id=str(ids[3]),reason='Synthetic private correction',
        private_unpaid_confirmed='yes',private_unpaid_note='Synthetic clarification: no private payments')
    values.update(updates); return values


def test_hide_show_retry_undo_and_aba_never_change_payment_data(app,client,private_round):
    before=finance(app); first=token(app,private_round)
    assert '84.00' in client.get('/dashboard/').text
    response=toggle(client,private_round,first)
    assert response.status_code==302 and 'hidden_reminder=' in response.location
    body=client.get(response.location).text
    assert '84.00' not in body and 'Rückgängig: Erinnerung wieder anzeigen' in body
    assert toggle(client,private_round,first).status_code==302
    assert '84.00' in client.get(f'/events/{private_round[1]}?tab=billbro').text
    assert 'Erinnerung wieder anzeigen' in client.get('/member/private-reminders').text
    second=token(app,private_round)
    assert toggle(client,private_round,second,'show').status_code==302
    assert toggle(client,private_round,first).status_code==400
    assert finance(app)==before
    with app.app_context():
        claim=db.session.get(MemberClaim,private_round[2])
        assert not claim.private_reminder_hidden and claim.private_reminder_version==2


@pytest.mark.parametrize('change',['amount','payer','title','same_amount'])
def test_correction_changes_only_relevant_preferences(app,client,private_round,change):
    assert toggle(client,private_round,token(app,private_round)).status_code==302
    values=private_form(private_round)
    if change=='title':
        with app.app_context(): db.session.get(Event,private_round[1]).restaurant='Changed title only'; db.session.commit()
    else:
        if change=='amount': values['total']='270'
        if change=='same_amount': values['invoice']='105'
        if change=='payer':
            with app.app_context(): values['payer_member_id']=str(Member.query.filter(Member.id.notin_([private_round[0],private_round[3]])).first().id)
        assert confirm(client,private_round,preview(client,private_round,values)).status_code==302
    with app.app_context():
        claim=MemberClaim.query.filter_by(member_id=private_round[0]).one()
        assert claim.private_reminder_hidden is (change in ('title','same_amount'))
        if change in ('amount','payer'): assert claim.private_reminder_changed
        assert claim.paid_rappen==0 and claim.status==ClaimStatus.OFFEN
    assert ('84.00' in client.get('/dashboard/').text)==(change=='payer')
    if change=='amount': assert '90.00' in client.get('/dashboard/').text


def test_legacy_private_payment_is_not_rewritten_or_presented_as_verified(app,client,private_round):
    with app.app_context():
        claim=db.session.get(MemberClaim,private_round[2]); claim.paid_rappen=8400; claim.status=ClaimStatus.BEGLICHEN; db.session.commit()
    before=finance(app)
    body=client.get('/member/private-reminders').text
    assert '84.00' in body and 'keine Zahlungsbestätigung' in body and 'Beglichen' not in body
    assert toggle(client,private_round,token(app,private_round)).status_code==302
    assert finance(app)==before
    assert client.post(f'/accounting/claims/{private_round[2]}/confirm').status_code==410
    assert finance(app)==before
    with app.app_context():
        assert AccountingService.get_open_claims_for_member(db.session.get(Member,private_round[0]))==[]
        assert AccountingService.get_claims_overview()==[]
        with pytest.raises(AccountingValidationError): AccountingService.confirm_private_payment(private_round[2],db.session.get(Member,private_round[3]))
        with pytest.raises(AccountingValidationError): AccountingService.settle_claim(private_round[2])


@pytest.mark.parametrize('case',['other_member','payer','tamper','expired','generation','wrong_action','changed_amount','csrf'])
def test_stale_foreign_or_invalid_toggle_changes_nothing(app,client,private_round,monkeypatch,case):
    tok=token(app,private_round); action='hide'
    if case in ('other_member','payer'):
        with app.app_context():
            mid=private_round[3] if case=='payer' else Member.query.filter(Member.id.notin_([private_round[0],private_round[3]])).first().id
        with client.session_transaction() as state: state['_user_id']=auth_id(client,mid); state['_fresh']=True
    if case=='tamper': tok+='invalid'
    if case=='expired':
        from itsdangerous.timed import TimestampSigner
        original=TimestampSigner.get_timestamp
        monkeypatch.setattr(TimestampSigner,'get_timestamp',lambda self: original(self)+1900)
    if case=='generation':
        with app.app_context(): db.session.get(Member,private_round[0]).rotate_auth_generation(); db.session.commit()
        with client.session_transaction() as state: state['_user_id']=auth_id(client,private_round[0]); state['_fresh']=True
    if case=='wrong_action': action='show'
    if case=='changed_amount':
        with app.app_context(): db.session.get(MemberClaim,private_round[2]).expected_rappen+=1; db.session.commit()
    if case=='csrf': app.config['WTF_CSRF_ENABLED']=True
    before=finance(app)
    assert toggle(client,private_round,tok,action).status_code==400
    assert finance(app)==before
    with app.app_context(): assert not db.session.get(MemberClaim,private_round[2]).private_reminder_hidden


@pytest.mark.parametrize('failure',['update','commit'])
def test_toggle_storage_failure_rolls_back_preference_and_finances(app,client,private_round,monkeypatch,failure):
    tok=token(app,private_round); before=finance(app)
    def fail(*args): raise OperationalError('synthetic',{},Exception('synthetic'))
    if failure=='update': sa_event.listen(MemberClaim,'before_update',fail)
    try:
        with monkeypatch.context() as patch:
            if failure=='commit': patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            assert toggle(client,private_round,tok).status_code==400
    finally:
        if failure=='update': sa_event.remove(MemberClaim,'before_update',fail)
    assert finance(app)==before
    with app.app_context():
        claim=db.session.get(MemberClaim,private_round[2]); assert claim.private_reminder_version==0 and not claim.private_reminder_hidden
    assert toggle(client,private_round,tok).status_code==302


def test_hidden_event_keeps_only_own_amount_and_generic_label(app,client,private_round):
    with app.app_context():
        actor=db.session.get(Member,private_round[0]); actor.role=Role.MEMBER
        event=db.session.get(Event,private_round[1]); event.audience=EventAudience.BOARD
        event.organisator_id=private_round[3]; event.restaurant='SECRET-BOARD-TITLE'; db.session.commit()
    response=client.get('/member/private-reminders')
    assert response.status_code==200 and '84.00' in response.text and 'Geschuetztes Event' in response.text
    assert 'SECRET-BOARD-TITLE' not in response.text and f'/events/{private_round[1]}' not in response.text
    assert toggle(client,private_round,token(app,private_round),return_to='event').location.endswith('/member/private-reminders')


def test_club_transition_creates_no_private_payment_proof(app,client,private_round):
    assert toggle(client,private_round,token(app,private_round)).status_code==302
    values=private_form(private_round,paid_by='vereinskonto',payer_member_id='')
    assert confirm(client,private_round,preview(client,private_round,values)).status_code==302
    with app.app_context():
        claims=MemberClaim.query.all()
        assert all(c.is_club_claim and c.paid_rappen==0 and not c.private_reminder_hidden for c in claims)
        assert Service.rows(db.session.get(Member,private_round[0]),include_hidden=True)==[]


def test_erlass_stays_excluded_and_club_claim_cannot_be_hidden(app,client,private_round):
    from backend.models.accounting import ClaimType
    with app.app_context():
        private=db.session.get(MemberClaim,private_round[2]); private.status=ClaimStatus.ERLASSEN
        club=MemberClaim(member_id=private_round[0],claim_type=ClaimType.MITGLIEDERBEITRAG,expected_rappen=1000)
        db.session.add(club); db.session.commit()
        cid=club.id; forged_context_token=Service.token(club,db.session.get(Member,private_round[0]))
        assert Service.rows(db.session.get(Member,private_round[0]),include_hidden=True)==[]
    before=finance(app)
    assert client.post(f'/member/private-reminders/{cid}',data={'action':'hide','reminder_token':forged_context_token}).status_code==400
    assert finance(app)==before


def test_old_form_after_claim_replacement_cannot_hide_new_claim(app,client,private_round):
    tok=token(app,private_round)
    assert confirm(client,private_round,preview(client,private_round,private_form(private_round,total='270'))).status_code==302
    with app.app_context(): new_id=MemberClaim.query.filter_by(member_id=private_round[0]).one().id
    assert toggle(client,private_round,tok).status_code==400
    assert client.post(f'/member/private-reminders/{new_id}',data={'action':'hide','reminder_token':tok}).status_code==400
    with app.app_context(): assert not db.session.get(MemberClaim,new_id).private_reminder_hidden


def test_internal_claim_sync_keeps_same_values_and_resets_changed_amount(app,client,private_round):
    from backend.models.participation import Participation
    assert toggle(client,private_round,token(app,private_round)).status_code==302
    with app.app_context():
        event=db.session.get(Event,private_round[1]); claim=db.session.get(MemberClaim,private_round[2])
        AccountingService.create_claims_for_billbro(event)
        assert claim.private_reminder_hidden
        Participation.query.filter_by(member_id=private_round[0]).one().calculated_share_rappen+=1
        AccountingService.create_claims_for_billbro(event)
        assert not claim.private_reminder_hidden and claim.private_reminder_changed
        assert claim.paid_rappen==0 and claim.status==ClaimStatus.OFFEN


def test_return_target_is_local_and_gets_do_not_write(app,client,private_round):
    with app.app_context(): engine=db.engine
    writes=[]
    def capture(conn,cursor,sql,*args):
        if sql.lstrip().upper().startswith(('INSERT','UPDATE','DELETE')): writes.append(sql)
    sa_event.listen(engine,'before_cursor_execute',capture)
    try:
        for path in ['/dashboard/','/member/private-reminders',f'/events/{private_round[1]}?tab=billbro']:
            assert client.get(path).status_code==200
    finally: sa_event.remove(engine,'before_cursor_execute',capture)
    assert not writes
    response=toggle(client,private_round,token(app,private_round),return_to='https://example.invalid')
    assert response.status_code==302 and response.location=='/member/private-reminders'
