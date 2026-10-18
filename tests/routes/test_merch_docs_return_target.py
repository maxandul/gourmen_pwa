"""A-035: remaining documented Merch/Drive return paths; no live services."""

from datetime import datetime
from unittest.mock import Mock

from tests.conftest import auth_id
import pytest
from flask import session
from flask_wtf.csrf import generate_csrf

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.document import Document
from backend.models.merch_order import MerchOrder, OrderStatus
from backend.services.drive_storage import DriveStorageService, DriveError, DriveValidationError


@pytest.fixture
def records(app, client):
    with app.app_context():
        member = Member(password_changed_at=datetime(2026, 1, 1),
                        vorname='Redirect', nachname='Test', email='redirect@example.test',
                        passwort_hash='unused', role=Role.ADMIN)
        db.session.add(member)
        db.session.flush()
        doc = Document(drive_file_id='synthetic-file', drive_parent_id='synthetic-parent',
                       uploader_id=member.id)
        order = MerchOrder(member_id=member.id, order_number='SYNTHETIC-1',
                           total_member_price_rappen=100, total_supplier_price_rappen=100,
                           total_profit_rappen=0, status=OrderStatus.WIRD_GELIEFERT)
        db.session.add_all([doc, order])
        db.session.commit()
        ids = member.id, doc.id, order.id
    with app.test_request_context():
        token = generate_csrf()
        raw_token = session['csrf_token']
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, ids[0])
        state['_fresh'] = True
        state['csrf_token'] = raw_token
    return (*ids, token)


@pytest.mark.parametrize('action', ['rename', 'move', 'archive', 'restore'])
@pytest.mark.parametrize('outcome', ['success', 'validation', 'service_error', 'missing_folder'])
@pytest.mark.parametrize('target', ['https://example.invalid', '//example.invalid',
                                  '/docs/folder/local?view=list#files'])
def test_document_return_paths(app, client, records, monkeypatch, action, outcome, target):
    _, doc_id, _, token = records
    service = Mock()
    if outcome == 'validation':
        service.side_effect = DriveValidationError('Synthetic validation failure')
    elif outcome == 'service_error':
        service.side_effect = DriveError('Synthetic service failure')
    monkeypatch.setattr(DriveStorageService, action + '_document', service)
    app.config['DRIVE_ARCHIVE_FOLDER_ID'] = 'synthetic-archive'
    data = {'csrf_token': token, 'next': target, 'title': 'Synthetic title',
            'new_parent_id': 'synthetic-target', 'target_folder_id': 'synthetic-target'}
    if outcome == 'missing_folder':
        data.pop('new_parent_id')
        data.pop('target_folder_id')
    response = client.post(f'/docs/file/{doc_id}/{action}', data=data)
    assert response.status_code == 302
    success = outcome in ('success', 'missing_folder')
    if action == 'archive' and success:
        expected = '/docs/folder/synthetic-archive'
    elif action == 'restore' and outcome == 'success':
        expected = '/docs/folder/synthetic-target'
    elif target.startswith('/docs/'):
        expected = target
    else:
        expected = f'/docs/file/{doc_id}' if action == 'restore' else '/docs/folder/synthetic-parent'
    assert response.location == expected
    if outcome == 'missing_folder' and action in ('move', 'restore'):
        service.assert_not_called()
    else:
        service.assert_called_once()


@pytest.mark.parametrize('outcome', ['success', 'invalid', 'service_error'])
@pytest.mark.parametrize('target', ['https://example.invalid', '//example.invalid',
                                  '/admin/merch/orders?status=open#orders'])
def test_merch_return_paths(app, client, records, monkeypatch, outcome, target):
    _, _, order_id, token = records
    from backend.services.accounting import AccountingService
    from backend.models.merch_article import MerchArticle
    from backend.models.merch_variant import MerchVariant
    from backend.models.merch_order_item import MerchOrderItem
    with app.app_context():
        article = MerchArticle(name='Synthetic return', base_supplier_price_rappen=100, base_member_price_rappen=100)
        db.session.add(article); db.session.flush()
        variant = MerchVariant(article_id=article.id, color='Blue', size='M', supplier_price_rappen=100, member_price_rappen=100)
        db.session.add(variant); db.session.flush()
        item = MerchOrderItem(order_id=order_id, article_id=article.id, variant_id=variant.id,
                              quantity=1, unit_member_price_rappen=100, unit_supplier_price_rappen=100)
        item.calculate_totals(); db.session.add(item); db.session.commit()
    claim = Mock(side_effect=RuntimeError('Synthetic service error'))
    monkeypatch.setattr(AccountingService, 'create_claim_for_merch_order', claim)
    status = {'success': 'WIRD_GELIEFERT', 'invalid': 'INVALID', 'service_error': 'GELIEFERT'}[outcome]
    response = client.post(f'/admin/merch/orders/{order_id}/status',
                           data={'status': status, 'next': target, 'csrf_token': token})
    assert response.status_code == 302
    expected = target if target.startswith('/admin/') else f'/admin/merch/orders/{order_id}'
    assert response.location == expected
    with app.app_context():
        expected_status = 'WIRD_GELIEFERT'  # No-op, invalid or failed transition all preserve the original.
        assert db.session.get(MerchOrder, order_id).status.value == expected_status
    if outcome == 'service_error':
        claim.assert_called_once()
        assert claim.call_args.kwargs == {'commit': False}
    else:
        claim.assert_not_called()


@pytest.mark.parametrize('action', ['rename', 'move', 'archive', 'restore'])
def test_docs_require_csrf(client, records, monkeypatch, action):
    service = Mock()
    monkeypatch.setattr(DriveStorageService, action + '_document', service)
    response = client.post(f'/docs/file/{records[1]}/{action}', data={'next': '//example.invalid'})
    assert response.status_code == 403
    service.assert_not_called()


def test_merch_requires_admin(app, client, records):
    with app.app_context():
        db.session.get(Member, records[0]).role = Role.MEMBER
        db.session.commit()
    response = client.post(f'/admin/merch/orders/{records[2]}/status',
                           data={'status': 'BESTELLT', 'next': '//example.invalid'})
    assert response.status_code in (302, 403)
    assert response.location != '//example.invalid'
    with app.app_context():
        assert db.session.get(MerchOrder, records[2]).status == OrderStatus.WIRD_GELIEFERT
