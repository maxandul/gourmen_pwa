"""Persist-before-send and one-attempt recovery delivery, without any real mail."""
from datetime import timedelta
from unittest.mock import Mock
import pytest
from sqlalchemy.exc import SQLAlchemyError
from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.auth_token import AuthToken, AuthTokenPurpose as Purpose
from backend.services.recovery_links import RecoveryLinkService as Recovery
from backend.services.mail import MailService
from backend.services.security import SecurityService
from tests.routes.test_event_visibility import visibility_data,login


@pytest.fixture
def delivery_case(app,visibility_data,monkeypatch):
    members,_=visibility_data
    with app.app_context():
        db.session.get(Member,members[1]).email='reader@example.com'
        db.session.add(MemberMFA(member_id=members[1],is_totp_enabled=True,totp_secret_encrypted='synthetic'))
        db.session.commit()
    send=Mock(return_value={'success':True,'message_id':'synthetic-message-id'});monkeypatch.setattr(MailService,'send',send)
    return members,send


@pytest.mark.parametrize('purpose',[Purpose.PASSWORD_RESET,Purpose.MFA_RESET])
def test_persisted_claim_and_fixed_recipient(app,delivery_case,purpose):
    members,send=delivery_case
    def delivered(**kwargs):
        db.session.expire_all();row=AuthToken.query.filter_by(member_id=members[1],purpose=purpose).one()
        assert row.id and row.delivery_status=='sending'
        assert kwargs['to']==row.recipient_email=='reader@example.com'
        # A concurrent address change cannot redirect the immutable outgoing message.
        member=db.session.get(Member,members[1]);SecurityService.update_primary_email(member,'later@example.com');db.session.commit()
        assert kwargs['to']=='reader@example.com'
        return {'success':True,'message_id':'synthetic-message-id'}
    send.side_effect=delivered
    with app.test_request_context():
        assert Recovery.request(members[1],purpose,None)=='accepted'
        assert AuthToken.query.one().used_at is not None


@pytest.mark.parametrize('failure',['structured','exception'])
def test_unconfirmed_is_durable_and_never_retried(app,delivery_case,failure):
    members,send=delivery_case
    send.return_value={'success':False}
    if failure=='exception':send.side_effect=RuntimeError('synthetic lost response')
    with app.test_request_context():
        raw,row=Recovery.prepare(members[1],Purpose.PASSWORD_RESET,timedelta(hours=1),None);db.session.commit();tid=row.id
        assert Recovery.deliver(tid,raw)=='unconfirmed'
        assert Recovery.deliver(tid,raw)=='unconfirmed'
        assert send.call_count==1


@pytest.mark.parametrize('failure',['issue','claim','result'])
def test_commit_boundaries(app,delivery_case,monkeypatch,failure):
    members,send=delivery_case
    with app.test_request_context():
        raw,old=Recovery.prepare(members[1],Purpose.PASSWORD_RESET,timedelta(hours=1),None);db.session.commit();old_id=old.id
        original=db.session.commit;calls=[]
        def commit():
            calls.append(True)
            if len(calls)=={'issue':1,'claim':2,'result':3}[failure]:raise SQLAlchemyError('synthetic commit failure')
            return original()
        monkeypatch.setattr(db.session,'commit',commit)
        expected={'issue':'unconfirmed','claim':'pending','result':'sending'}[failure]
        assert Recovery.request(members[1],Purpose.PASSWORD_RESET,None)==expected
        assert send.call_count==int(failure=='result')
        if failure=='issue':
            assert AuthToken.query.count()==1 and db.session.get(AuthToken,old_id).used_at is None
        else:
            row=AuthToken.query.order_by(AuthToken.id.desc()).first();assert row.delivery_status==expected
            if failure=='result':
                assert Recovery.deliver(row.id,'irrelevant')=='sending'
                assert send.call_count==1


def test_obsolete_recipient_never_reaches_mail(app,delivery_case):
    members,send=delivery_case
    with app.test_request_context():
        raw,row=Recovery.prepare(members[1],Purpose.MFA_RESET,timedelta(hours=1),None);db.session.commit();tid=row.id
        SecurityService.update_primary_email(db.session.get(Member,members[1]),'later@example.com');db.session.commit()
        assert Recovery.deliver(tid,raw)=='obsolete';send.assert_not_called()


def test_neutral_public_response_and_admin_status_without_secrets(app,client,delivery_case):
    members,send=delivery_case
    for email in ['reader@example.com','unknown@example.com']:
        assert client.post('/auth/forgot-password',data={'email':email}).status_code==302
        with client.session_transaction() as state:
            message=state['_flashes'][-1][1]
            assert 'Wenn die Adresse' in message and 'reader@example.com' not in message
    assert send.call_count==1
    with app.app_context():token_hash=AuthToken.query.one().token_hash
    raw=send.call_args.kwargs['text'].split('/reset-password/')[1].split()[0]
    login(client,members[1]);assert client.get(f'/admin/members/{members[1]}/recovery-links').status_code==403
    login(client,members[3]);response=client.get(f'/admin/members/{members[1]}/recovery-links')
    assert response.status_code==200 and response.headers['Cache-Control']=='no-store'
    body=response.get_data(as_text=True)
    assert 'Vom Maildienst angenommen' in body and token_hash not in body and raw not in body


def test_skipped_mail_is_not_success(app,monkeypatch):
    with app.app_context():
        app.config.update(RESEND_API_KEY='',MAIL_SMTP_HOST=None)
        assert MailService.send(to='synthetic@example.com',subject='Test',html='synthetic')['success'] is False
        app.config.update(MAIL_SMTP_HOST='smtp.invalid',MAIL_SMTP_USERNAME='',MAIL_SMTP_PASSWORD='')
        assert MailService.send(to='synthetic@example.com',subject='Test',html='synthetic')['success'] is False


def test_provider_cannot_echo_recovery_link_into_logs(app,monkeypatch,caplog):
    from types import SimpleNamespace
    secret='synthetic-private-link-marker'
    response=SimpleNamespace(ok=False,status_code=400,text=secret,json=lambda:{'message':secret})
    monkeypatch.setattr('backend.services.mail.requests.post',lambda *a,**k:response)
    with app.app_context():
        app.config['RESEND_API_KEY']='synthetic-key'
        result=MailService.send(to='synthetic@example.com',subject='Test',html=secret,tags={'type':'password_reset'})
        assert result['success'] is False and result['error']=='resend_rejected'
    assert secret not in caplog.text
