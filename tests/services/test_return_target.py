"""Internal URL contract used by password and MFA login."""
import pytest

from backend.services.security import SecurityService


@pytest.mark.parametrize('value', [None, 123, '', 'profile', 'https://example.invalid',
                                 '//example.invalid', '///example.invalid',
                                 '/\\example.invalid', '/%2Fexample.invalid',
                                 '/%5Cexample.invalid', '/%0d%0aLocation:evil',
                                 '/\x00evil', '/\tevil', '/\x7fevil', '//[invalid'])
def test_reject_unsafe_target(value):
    assert SecurityService.local_return_target(value) is None


@pytest.mark.parametrize('value', ['/', '/member/profile', '/events/42?tab=details#bill',
                                 '/docs/?q=Z%C3%BCrich', '/docs/?q=https://example.invalid'])
def test_preserve_local_target(value):
    assert SecurityService.local_return_target(value) == value
