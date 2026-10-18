"""Receipt/document selection rights, synthetic SQLite and fake Drive only."""
from datetime import date
from io import BytesIO
from types import SimpleNamespace
import pytest
from werkzeug.datastructures import FileStorage
from backend.extensions import db
from backend.models.member import Member, Role, Funktion
from backend.models.accounting import Account, AccountKind, FiscalYear, Booking, BookingDirection, Receipt
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.drive_storage import DriveStorageService, DriveValidationError, FolderListing
from tests.routes.test_event_visibility import visibility_data, login


@pytest.fixture
def selection_data(app,visibility_data):
    members,events=visibility_data
    with app.app_context():
        fy=FiscalYear(year=date.today().year, start_date=date(date.today().year,1,1), end_date=date(date.today().year,12,31))
        account=Account(code='5000',name='Synthetic category',kind=AccountKind.EXPENSE)
        db.session.add_all([fy,account]);db.session.flush()
        bookings=[]
        for eid in [events[0],events[2]]:
            b=Booking(fiscal_year_id=fy.id,booking_date=date.today(),description=f'secret-booking-{eid}',
                      amount_rappen=98765,direction=BookingDirection.OUT,account_id=account.id,
                      event_id=eid,created_by=members[0])
            db.session.add(b);db.session.flush();bookings.append(b.id)
        db.session.commit()
        return members,events,bookings,fy.id


@pytest.mark.parametrize('role,allowed', [('member',False),('board',False),('reviewer',False),('treasurer',True),('admin',True)])
def test_receipt_options_and_query_context(app,client,selection_data,role,allowed):
    members,events,bookings,_=selection_data
    with app.app_context():
        member=db.session.get(Member,members[1])
        member.role=Role.ADMIN if role=='admin' else Role.MEMBER
        member.vorstandsmitglied=role=='board'
        member.funktion={'reviewer':Funktion.RECHNUNGSPRUEFER,'treasurer':Funktion.SCHATZMEISTER}.get(role,Funktion.MEMBER)
        db.session.commit()
    login(client,members[1]);response=client.get('/accounting/receipt/upload');assert response.status_code==200
    body=response.get_data(as_text=True)
    assert (f'secret-booking-{events[0]}' in body)==allowed
    assert ('board-past-private-marker' in body)==(role in ['board','admin'])
    assert (f'secret-booking-{events[2]}' in body)==(role=='admin')
    assert client.get(f'/accounting/receipt/upload?booking={bookings[0]}').status_code==(200 if allowed else 403)


@pytest.mark.parametrize('field', ['booking_id','suggested_event_id'])
def test_forged_receipt_post_never_reaches_upload(app,client,selection_data,monkeypatch,field):
    members,events,bookings,_=selection_data; login(client,members[1])
    def forbidden(**kwargs): pytest.fail('Forbidden upload reached service')
    monkeypatch.setattr(AccountingService,'upload_receipt',forbidden)
    data={'file':(BytesIO(b'synthetic'),'test.pdf'),'suggested_account_id':'0','suggested_event_id':'0','booking_id':'0'}
    data[field]=str(bookings[0] if field=='booking_id' else events[2])
    assert client.post('/accounting/receipt/upload',data=data).status_code==200
    with app.app_context():assert Receipt.query.count()==0


def test_service_rechecks_selection_and_allows_unlinked_own_receipt(app,selection_data,monkeypatch):
    members,events,bookings,fy=selection_data
    calls=[]
    monkeypatch.setattr(DriveStorageService,'upload_bytes',lambda **kw: calls.append(kw) or {'id':'synthetic-file','name':'test.pdf'})
    monkeypatch.setattr(AccountingService,'get_receipt_folder_id',lambda year:'synthetic-folder')
    with app.app_context():
        member=db.session.get(Member,members[1])
        for extra in [{'booking_id':bookings[0]},{'suggested_event_id':events[2]},{'suggested_event_id':99999}]:
            with pytest.raises(AccountingValidationError):
                AccountingService.upload_receipt(FileStorage(stream=BytesIO(b'x'),filename='test.pdf'),member,fy,**extra)
        assert calls==[]
        receipt=AccountingService.upload_receipt(FileStorage(stream=BytesIO(b'x'),filename='test.pdf',content_type='application/pdf'),member,fy,suggested_event_id=events[0])
        assert receipt.uploader_id==member.id and receipt.booking_id is None
        assert len(calls)==1


def test_treasurer_can_link_visible_booking_but_not_board_booking(app,selection_data,monkeypatch):
    members,events,bookings,fy=selection_data
    monkeypatch.setattr(DriveStorageService,'upload_bytes',lambda **kw:{'id':'synthetic-linked','name':'test.pdf'})
    monkeypatch.setattr(AccountingService,'get_receipt_folder_id',lambda year:'synthetic-folder')
    with app.app_context():
        member=db.session.get(Member,members[1]);member.funktion=Funktion.SCHATZMEISTER;db.session.commit()
        with pytest.raises(AccountingValidationError):
            AccountingService.upload_receipt(FileStorage(stream=BytesIO(b'x'),filename='test.pdf'),member,fy,booking_id=bookings[1])
        receipt=AccountingService.upload_receipt(FileStorage(stream=BytesIO(b'x'),filename='test.pdf'),member,fy,booking_id=bookings[0])
        assert receipt.booking_id==bookings[0]


def test_document_options_and_forged_event(app,client,selection_data,monkeypatch):
    members,events,_,_=selection_data;login(client,members[1])
    app.config['GOOGLE_DRIVE_ID']='synthetic-root'
    monkeypatch.setattr(DriveStorageService,'list_folder',lambda *args:FolderListing(folder_id='synthetic-root',subfolders=[],files=[]))
    monkeypatch.setattr(DriveStorageService,'get_folder_breadcrumb',lambda *args:[])
    monkeypatch.setattr(DriveStorageService,'get_web_view_link_for_folder_id',lambda *args:'')
    for path in ['/docs/','/docs/folder/synthetic-root']:
        response=client.get(path);assert response.status_code==200
        assert 'all-past-private-marker' in response.get_data(as_text=True)
        assert 'board-past-private-marker' not in response.get_data(as_text=True)
    # CSRF remains separate; bypass only its validator to exercise permission branch.
    monkeypatch.setattr('backend.routes.docs._validate_csrf_or_403',lambda:None)
    monkeypatch.setattr(DriveStorageService,'upload_document',lambda **kw:pytest.fail('Forbidden document upload'))
    for eid in [events[2],99999]:
        assert client.post('/docs/upload',data={'file':(BytesIO(b'x'),'test.pdf'),'drive_folder_id':'synthetic-root','event_id':str(eid)}).status_code==403


def test_document_service_checks_before_drive(app,selection_data,monkeypatch):
    members,events,_,_=selection_data
    monkeypatch.setattr(DriveStorageService,'assert_is_folder_in_drive',lambda *args:pytest.fail('Drive must not be reached'))
    with app.app_context():
        with pytest.raises(DriveValidationError):
            DriveStorageService.upload_document(BytesIO(b'x'),'test','folder',db.session.get(Member,members[1]),event_id=events[2])


def test_receipt_selection_and_forged_attachment_enforce_event_rights(app,client,selection_data,monkeypatch):
    members,events,bookings,fy=selection_data
    with app.app_context():
        actor=db.session.get(Member,members[1]);actor.funktion=Funktion.SCHATZMEISTER
        receipt=Receipt(drive_file_id='hidden',drive_file_name='secret-receipt-marker',drive_folder_id='folder',
                        file_type='application/pdf',uploader_id=members[0],suggested_event_id=events[2])
        db.session.add(receipt);db.session.commit();rid=receipt.id
        with pytest.raises(AccountingValidationError):
            AccountingService.attach_receipt_to_booking(rid,bookings[0],actor)
        assert receipt.booking_id is None
    login(client,members[1])
    response=client.get(f'/accounting/booking/{bookings[0]}');assert response.status_code==200
    assert 'secret-receipt-marker' not in response.get_data(as_text=True)
    assert client.get(f'/accounting/receipt/{rid}').status_code==403
    assert client.get(f'/accounting/booking/new?receipt={rid}').status_code==403
