"""A-113: test dispatch requires explicit availability and cron authentication."""

from unittest.mock import Mock

import pytest
from flask import Flask

from backend.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig


TOKEN = 'synthetic-cron-token'


@pytest.fixture
def cron_case(app, monkeypatch):
    # Use real configuration classes without creating a production DB connection.
    from backend.routes.cron import bp, CronService

    dispatch = Mock(return_value={'success': True, 'sent_count': 0})
    monkeypatch.setattr(CronService, 'run_3_week_reminders', dispatch)

    def make(config=ProductionConfig, **overrides):
        isolated = Flask(__name__)
        isolated.config.from_object(config)
        isolated.config.update(CRON_AUTH_TOKEN=TOKEN)
        isolated.config.update(overrides)
        isolated.register_blueprint(bp)
        return isolated.test_client(), dispatch

    return make


@pytest.mark.parametrize('config', [Config, ProductionConfig, TestingConfig])
@pytest.mark.parametrize('authenticated', [False, True])
def test_test_endpoint_disabled_by_default(cron_case, config, authenticated):
    client, dispatch = cron_case(config)
    response = client.post('/cron/test', headers={'X-Cron-Auth': TOKEN} if authenticated else {})
    assert response.status_code == 403
    dispatch.assert_not_called()


@pytest.mark.parametrize('value', [None, False, 'true', 'false', 1])
def test_only_explicit_boolean_enables_test_endpoint(cron_case, value):
    client, dispatch = cron_case(CRON_TEST_ENABLED=value)
    assert client.post('/cron/test', headers={'X-Cron-Auth': TOKEN}).status_code == 403
    dispatch.assert_not_called()


@pytest.mark.parametrize('overrides', [{'DEBUG': True}, {'ENV': 'development'}, {'TESTING': True}])
def test_unrelated_flags_do_not_enable_production_test_endpoint(cron_case, overrides):
    client, dispatch = cron_case(**overrides)
    assert client.post('/cron/test', headers={'X-Cron-Auth': TOKEN}).status_code == 403
    dispatch.assert_not_called()


@pytest.mark.parametrize('credential', ['missing', 'wrong', 'missing_config'])
def test_development_test_dispatch_requires_token(cron_case, credential):
    overrides = {'CRON_AUTH_TOKEN': None} if credential == 'missing_config' else {}
    client, dispatch = cron_case(DevelopmentConfig, **overrides)
    headers = {'X-Cron-Auth': 'wrong'} if credential == 'wrong' else {}
    assert client.post('/cron/test', headers=headers).status_code == 401
    dispatch.assert_not_called()


@pytest.mark.parametrize('transport', ['header', 'bearer', 'query'])
def test_explicit_enabled_and_authenticated_dispatch(cron_case, transport, caplog):
    client, dispatch = cron_case(CRON_TEST_ENABLED=True)
    kwargs = {}
    if transport == 'header':
        kwargs['headers'] = {'X-Cron-Auth': TOKEN}
    elif transport == 'bearer':
        kwargs['headers'] = {'Authorization': f'Bearer {TOKEN}'}
    else:
        kwargs['query_string'] = {'token': TOKEN}
    response = client.post('/cron/test', **kwargs)
    assert response.status_code == 200
    assert response.json['result'] == {'success': True, 'sent_count': 0}
    dispatch.assert_called_once_with()
    assert TOKEN not in caplog.text


def test_development_authorized_dispatch_still_works(cron_case):
    client, dispatch = cron_case(DevelopmentConfig)
    assert client.post('/cron/test', headers={'X-Cron-Auth': TOKEN}).status_code == 200
    dispatch.assert_called_once_with()


@pytest.mark.parametrize('authorized', [False, True])
def test_regular_production_cron_contract_unchanged(cron_case, authorized):
    client, dispatch = cron_case()
    response = client.post('/cron/3-week-reminders', headers={'X-Cron-Auth': TOKEN} if authorized else {})
    assert response.status_code == (200 if authorized else 401)
    assert dispatch.call_count == int(authorized)


def test_regular_local_cron_without_token_keeps_existing_behavior(cron_case):
    client, dispatch = cron_case(DevelopmentConfig, CRON_AUTH_TOKEN=None)
    assert client.post('/cron/3-week-reminders').status_code == 200
    dispatch.assert_called_once_with()


def test_get_cannot_execute_test_dispatch(cron_case):
    client, dispatch = cron_case(CRON_TEST_ENABLED=True)
    assert client.get('/cron/test', headers={'X-Cron-Auth': TOKEN}).status_code == 405
    dispatch.assert_not_called()
