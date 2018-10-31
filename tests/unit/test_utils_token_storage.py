import copy
from time import time

import pytest

from globus_sdk import config
from globus_sdk.exc import ConfigError, LoadedTokensExpired, RequestedScopesMismatch
from globus_sdk.utils.token_storage import clear_tokens, load_tokens, save_tokens

try:
    import mock
except ImportError:
    from unittest import mock

TOKEN_LIFETIME = 60 * 60 * 24

MOCK_TOKENS = {
    "auth.globus.org": {
        "scope": "profile openid email",
        "access_token": "9d0e6f2a21917cc3e04602838e0ba4f7df3399bbd49f1"
        "5db3cf0af34d52c928f34f639444af0b28695086d97b1",
        "refresh_token": None,
        "token_type": "Bearer",
        "expires_at_seconds": int(time()) + TOKEN_LIFETIME,
        "resource_server": "auth.globus.org",
    },
    "workhorse.org": {
        "scope": "all",
        "access_token": "QmFkIEhvcnNlLCBCYWQgSG9yc2UuIEJhZCBIb3JzZSwg"
        "QmFkIEhvcnNlLiBIZSByaWRlcyBhY3Jvc3MgdGhlIG5h",
        "refresh_token": "VGhlIGV2aWwgbGVhZ3VlIG9mIGV2aWwsIGlzIHdhdGNo"
        "aW5nIHNvIGJld2FyZS4gVGhlIGdyYWRlIHRoYXQgeW8=",
        "token_type": "Bearer",
        "expires_at_seconds": int(time()) + TOKEN_LIFETIME,
        "resource_server": "workhorse.org",
    },
}


@pytest.fixture
def mock_expired_tokens():
    expired_tokens = copy.deepcopy(MOCK_TOKENS)
    for _, token_set in expired_tokens.items():
        token_set["expires_at_seconds"] = int(time()) - 1
    return expired_tokens


@pytest.fixture
def mock_native_app(monkeypatch):
    mock_client = mock.MagicMock()
    monkeypatch.setattr(
        "globus_sdk.utils.token_storage.NativeAppAuthClient", mock_client
    )
    return mock_client


def test_save_and_load_tokens_matches_original(temp_config):
    save_tokens(MOCK_TOKENS, "test")
    tokens = load_tokens("test")
    for set_name, set_values in tokens.items():
        loaded_set = set(set_values.values())
        mock_set = set(MOCK_TOKENS[set_name].values())
        assert not loaded_set.difference(mock_set)


def test_loading_bad_tokens_raises_error(temp_config):
    save_tokens(MOCK_TOKENS, "test")
    temp_config.remove("workhorse_org_access_token", "test")
    with pytest.raises(ConfigError):
        load_tokens("test")


def test_loading_raises_error_if_tokens_expire(temp_config, mock_expired_tokens):
    save_tokens(mock_expired_tokens, "test")
    with pytest.raises(LoadedTokensExpired):
        load_tokens("test")


def test_loading_raises_error_if_scopes_differ(temp_config):
    save_tokens(MOCK_TOKENS, "test")
    transfer_scope = ("urn:globus:auth:scope:transfer.api.globus.org:all",)
    with pytest.raises(RequestedScopesMismatch):
        load_tokens("test", requested_scopes=transfer_scope)


def test_verify_clear_tokens(temp_config, mock_native_app):
    save_tokens(MOCK_TOKENS, "test")
    section = config.get_parser().get_section("test")
    assert len(section.values()) == 13
    return_value = clear_tokens("test", "my_client_id")
    section = config.get_parser().get_section("test")
    assert len(section.values()) == 0
    mock_native_app.assert_called_with("my_client_id")
    assert return_value is True


def test_clear_tokens_with_no_saved_tokens(temp_config, mock_native_app):
    return_value = clear_tokens("test", "my_client_id")
    assert return_value is False


def test_clear_expired_tokens(temp_config, mock_expired_tokens, mock_native_app):
    save_tokens(mock_expired_tokens, "test")
    section = config.get_parser().get_section("test")
    assert len(section.values()) == 13
    return_value = clear_tokens("test", "my_client_id")
    section = config.get_parser().get_section("test")
    assert len(section.values()) == 0
    mock_native_app.assert_called_with("my_client_id")
    assert return_value is True


def test_clear_tokens_with_invalid_client_raises_error(temp_config):
    save_tokens(MOCK_TOKENS, "test")
    config.get_parser().remove("workhorse_org_access_token", "test")
    with pytest.raises(ConfigError):
        load_tokens("test")
