"""No network: simulate paginated permissions and uncertain API outcomes."""
from unittest.mock import Mock

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response

from backend.services.drive_storage import DriveStorageService, DriveError


def permission(pid='p1', email='old@example.com', kind='user'):
    return {'id': pid, 'emailAddress': email, 'type': kind, 'role': 'fileOrganizer'}


def http_error(status):
    return HttpError(Response({'status': str(status)}), b'{"error":"synthetic"}')


@pytest.fixture
def api(monkeypatch):
    drive = Mock()
    monkeypatch.setattr(DriveStorageService, '_build_drive', lambda: drive)
    return drive.permissions.return_value


def test_paginated_revoke_removes_all_matching_users_only(api):
    api.list.return_value.execute.side_effect = [
        {'permissions': [permission('other', 'other@example.com')], 'nextPageToken': 'next'},
        {'permissions': [permission('p1'), permission('group', kind='group'), permission('p2')]},
        {'permissions': []},
    ]
    DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')
    assert [call.kwargs['permissionId'] for call in api.delete.call_args_list] == ['p1', 'p2']
    assert api.list.call_args_list[1].kwargs['pageToken'] == 'next'
    assert all(call.kwargs['fileId'] == 'saved-drive' for call in api.list.call_args_list)


def test_absent_permission_is_idempotent_success(api):
    api.list.return_value.execute.return_value = {'permissions': []}
    for _ in range(2):
        DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')
    api.delete.assert_not_called()


@pytest.mark.parametrize('status', [403, 404, 429, 503])
def test_list_errors_are_never_successful_revocation(api, status):
    api.list.return_value.execute.side_effect = http_error(status)
    with pytest.raises(HttpError):
        DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')
    api.delete.assert_not_called()


def test_delete_404_requires_successful_follow_up_list(api):
    api.list.return_value.execute.side_effect = [
        {'permissions': [permission()]}, {'permissions': []}, {'permissions': []},
    ]
    api.delete.return_value.execute.side_effect = http_error(404)
    DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')
    assert api.list.call_count == 3


@pytest.mark.parametrize('follow_up', [http_error(404), {'permissions': [permission()]}])
def test_delete_404_with_unconfirmed_absence_stays_failed(api, follow_up):
    api.list.return_value.execute.side_effect = [{'permissions': [permission()]}, follow_up]
    api.delete.return_value.execute.side_effect = http_error(404)
    with pytest.raises(HttpError):
        DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')


def test_partial_delete_can_be_retried(api):
    api.list.return_value.execute.side_effect = [
        {'permissions': [permission('p1'), permission('p2')]},
        {'permissions': [permission('p2')]}, {'permissions': []},
    ]
    api.delete.return_value.execute.side_effect = [None, http_error(503), None]
    with pytest.raises(HttpError):
        DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')
    DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')
    assert [call.kwargs['permissionId'] for call in api.delete.call_args_list] == ['p1', 'p2', 'p2']


def test_revoke_requires_final_absence(api):
    api.list.return_value.execute.return_value = {'permissions': [permission()]}
    with pytest.raises(DriveError):
        DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')


def test_invite_retry_does_not_duplicate_permission_or_send_notification(api):
    api.list.return_value.execute.side_effect = [
        {'permissions': []}, {'permissions': [permission()]},
    ]
    for _ in range(2):
        DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'invite')
    api.create.assert_called_once()
    assert api.create.call_args.kwargs['sendNotificationEmail'] is False
    assert api.create.call_args.kwargs['body']['role'] == 'fileOrganizer'


def test_later_list_page_failure_does_not_delete_partial_results(api):
    api.list.return_value.execute.side_effect = [
        {'permissions': [permission()], 'nextPageToken': 'more'}, http_error(503),
    ]
    with pytest.raises(HttpError):
        DriveStorageService.apply_membership('saved-drive', 'old@example.com', 'revoke')
    api.delete.assert_not_called()
