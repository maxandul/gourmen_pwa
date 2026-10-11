"""U1b: synthetic secrets must not reach application log records."""

import logging
from unittest.mock import Mock

import pyotp
import pytest
import requests
from flask_login import login_user

from backend.services.places import PlacesService
from backend.models.member import Member
from backend.services.security import SecurityService, require_step_up


def assert_not_logged(caplog, *secrets):
    # Include raw arguments and traceback data, not just the formatted message.
    records = '\n'.join(str(record.__dict__) for record in caplog.records)
    for secret in secrets:
        assert secret not in caplog.text
        assert secret not in records


@pytest.mark.parametrize('valid', [False, True])
def test_totp_result_without_secret_or_codes(app, caplog, valid):
    secret = pyotp.random_base32()
    current_code = pyotp.TOTP(secret).now()
    token = current_code if valid else 'bad-code'
    with app.app_context(), caplog.at_level(logging.DEBUG):
        assert SecurityService.verify_totp(secret, token) is valid
    assert_not_logged(caplog, secret, current_code, token)


@pytest.mark.parametrize('method', ['autocomplete', 'get_place_details'])
@pytest.mark.parametrize('outcome', ['ok', 'api_error', 'http_error', 'connection_error', 'json_error'])
def test_places_logs_exclude_request_and_response_secrets(app, monkeypatch, caplog, method, outcome):
    api_key = 'synthetic-api-key-private'
    session_token = 'synthetic-session-token-private'
    query = 'synthetic-query-private'
    marker = f'{api_key} {session_token} {query}'
    payload = {'status': 'OK', 'predictions': [{'description': marker}], 'result': {'name': marker}}
    response = Mock(status_code=200)
    response.json.return_value = payload
    get = Mock(return_value=response)
    if outcome == 'api_error':
        response.json.return_value = {'status': marker, 'error_message': marker}
    elif outcome == 'http_error':
        response.status_code = 403
        response.raise_for_status.side_effect = requests.HTTPError(f'403 URL?key={marker}')
    elif outcome == 'connection_error':
        get.side_effect = requests.ConnectionError(f'URL?key={marker}')
    elif outcome == 'json_error':
        response.json.side_effect = ValueError(marker)
    monkeypatch.setattr('backend.services.places.requests.get', get)
    app.config['GOOGLE_MAPS_API_KEY'] = api_key
    with app.app_context(), caplog.at_level(logging.INFO):
        result = getattr(PlacesService, method)(query, session_token)
    if outcome == 'ok':
        assert result == payload['predictions' if method == 'autocomplete' else 'result']
    else:
        assert result == ([] if method == 'autocomplete' else None)
        assert any(record.levelno >= logging.WARNING for record in caplog.records)
    # Logging removal must not strip the credentials from the actual API request.
    assert get.call_args.kwargs['params']['key'] == api_key
    assert get.call_args.kwargs['params']['sessiontoken'] == session_token
    assert_not_logged(caplog, api_key, session_token, query)


def test_step_up_guard_does_not_log_url_token(app, caplog):
    @require_step_up
    def protected():
        return 'allowed'

    with app.test_request_context('/protected?token=synthetic-url-secret'), caplog.at_level(logging.INFO):
        login_user(Member(id=123, is_active=True))
        SecurityService.grant_step_up_access()
        assert protected() == 'allowed'
    assert_not_logged(caplog, 'synthetic-url-secret')


@pytest.mark.parametrize('method', ['autocomplete', 'get_place_details'])
def test_places_without_key_keeps_existing_fallback(app, monkeypatch, caplog, method):
    app.config['GOOGLE_MAPS_API_KEY'] = None
    get = Mock(side_effect=AssertionError('No network expected without key'))
    monkeypatch.setattr('backend.services.places.requests.get', get)
    fallback = Mock(return_value={'synthetic': 'fallback'})
    monkeypatch.setattr(PlacesService, '_get_mock_' + ('autocomplete' if method == 'autocomplete'
                                                     else 'place_details'), fallback)
    with app.app_context(), caplog.at_level(logging.INFO):
        assert getattr(PlacesService, method)('synthetic-input-private') == {'synthetic': 'fallback'}
    get.assert_not_called()
    fallback.assert_called_once_with('synthetic-input-private')
    assert_not_logged(caplog, 'synthetic-input-private')
