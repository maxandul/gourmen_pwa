"""Merch-Bild-Proxy GET /merch/image/<article_id>."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from werkzeug.security import generate_password_hash

import backend.models  # noqa: F401
from backend.extensions import db
from backend.models.member import Member
from backend.models.merch_v2 import MerchArticle, MerchSupplier


@pytest.fixture
def merch_v2_app_config(app, monkeypatch):
    monkeypatch.setitem(app.config, 'MERCH_V2_ENABLED', True)
    monkeypatch.setitem(app.config, 'MERCH_IMAGE_CACHE_TTL_SECONDS', 86400)


def _seed_article_with_image(image_file_id: str | None) -> int:
    m = Member(
        vorname='Merch',
        nachname='Tester',
        email='merch-img-test@example.test',
        passwort_hash=generate_password_hash('TestPasswortMind12'),
    )
    db.session.add(m)
    s = MerchSupplier(name='Proxy-Lieferant')
    db.session.add(s)
    db.session.flush()
    art = MerchArticle(
        name='Cap',
        supplier_id=s.id,
        list_price_rappen=1200,
        image_drive_file_id=image_file_id,
    )
    db.session.add(art)
    db.session.commit()
    return art.id


def test_merch_image_anonymous_redirects_to_login(client, app, merch_v2_app_config):
    with app.app_context():
        aid = _seed_article_with_image('drive-x')
    rv = client.get(f'/merch/image/{aid}')
    assert rv.status_code == 302


def test_merch_image_feature_off_returns_404(logged_in_client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'MERCH_V2_ENABLED', False)
    with app.app_context():
        aid = _seed_article_with_image('drive-x')
    rv = logged_in_client.get(f'/merch/image/{aid}')
    assert rv.status_code == 404


def test_merch_image_no_drive_file_returns_404(logged_in_client, app, merch_v2_app_config):
    with app.app_context():
        aid = _seed_article_with_image(None)
    rv = logged_in_client.get(f'/merch/image/{aid}')
    assert rv.status_code == 404


def test_merch_image_serves_from_mock_drive(
    logged_in_client,
    app,
    merch_v2_app_config,
    monkeypatch,
):
    mock_dl = Mock(
        return_value=(
            b'\x89PNG\r\n',
            'image/png',
            'cap.png',
            '2026-05-15T12:00:00.000Z',
        )
    )
    monkeypatch.setattr(
        'backend.services.drive_storage.DriveStorageService.download_binary_by_file_id',
        mock_dl,
    )
    with app.app_context():
        aid = _seed_article_with_image('drive-file-abc')

    rv = logged_in_client.get(f'/merch/image/{aid}')
    assert rv.status_code == 200
    assert rv.data.startswith(b'\x89PNG')
    assert rv.headers.get('Content-Type', '').startswith('image/png')
    assert 'ETag' in rv.headers
    assert mock_dl.call_count == 1

    etag = rv.headers['ETag'].strip('"')
    rv304 = logged_in_client.get(
        f'/merch/image/{aid}',
        headers={'If-None-Match': etag},
    )
    assert rv304.status_code == 304
    assert rv304.headers.get('ETag', '').strip('"') == etag
    # Ohne REDIS_URL wird der zweite Request erneut aus Drive geladen (ETag-Vergleich in der Route).
    assert mock_dl.call_count == 2


def test_merch_image_unknown_article_404(logged_in_client, merch_v2_app_config):
    rv = logged_in_client.get('/merch/image/999999')
    assert rv.status_code == 404
