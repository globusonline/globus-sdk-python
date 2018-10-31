import copy
import uuid
import webbrowser
from time import time

import pytest

import globus_sdk
from globus_sdk.auth import oauth2_native_app_shortcut
from globus_sdk.auth.oauth2_native_app_shortcut import (
    AUTH_CODE_REDIRECT,
    NATIVE_AUTH_DEFAULTS as NA_DEF,
    native_auth,
)
from globus_sdk.utils import token_storage

try:
    import mock
except ImportError:
    from unittest import mock

MOCK_TOKENS = {
    "auth.globus.org": {
        "scope": "profile openid email",
        "access_token": "9d0e6f2a21917cc3e04602838e0ba4f7df3399bbd49f1"
        "5db3cf0af34d52c928f34f639444af0b28695086d97b1",
        "refresh_token": None,
        "token_type": "Bearer",
        "expires_at_seconds": int(time()) + 60 * 60,
        "resource_server": "auth.globus.org",
    }
}

MOCK_AUTH_CODE = "foobarbaz"


@pytest.fixture
def mock_webbrowser(monkeypatch):
    monkeypatch.setattr(webbrowser, "open", mock.Mock())


@pytest.fixture
def mock_save_tokens(monkeypatch):
    mock_save = mock.Mock()
    monkeypatch.setattr(oauth2_native_app_shortcut, "save_tokens", mock_save)
    return mock_save


@pytest.fixture
def mock_clear_tokens(monkeypatch):
    mocked_clear_tokens = mock.Mock()
    monkeypatch.setattr(oauth2_native_app_shortcut, "clear_tokens", mocked_clear_tokens)
    return mocked_clear_tokens


@pytest.yield_fixture
def mock_local_server(monkeypatch):
    mock_server = mock.Mock()
    mock_server.__enter__ = mock.Mock(return_value=mock.Mock())
    mock_server.__exit__ = mock.Mock(return_value=mock.Mock())
    mock_start = mock.Mock(return_value=mock_server)
    monkeypatch.setattr(
        "globus_sdk.auth.oauth2_native_app_shortcut.start_local_server", mock_start
    )
    return mock_start


@pytest.fixture
def mock_native_client(monkeypatch):
    mock_client = mock.Mock()
    mock_class = mock.Mock(return_value=mock_client)
    token_response = mock.Mock()
    mock_client.oauth2_exchange_code_for_tokens.return_value = token_response
    token_response.by_resource_server = MOCK_TOKENS
    monkeypatch.setattr(
        "globus_sdk.auth.oauth2_native_app_shortcut.NativeAppAuthClient", mock_class
    )
    return mock_class, mock_client


@pytest.fixture
def mock_native_client_simple(mock_native_client):
    client_class, _ = mock_native_client
    return client_class


@pytest.yield_fixture
def saved_tokens(temp_config, mock_native_client):
    token_storage.save_tokens(MOCK_TOKENS, NA_DEF["client_id"])


@pytest.fixture
def expired_saved_tokens(temp_config):
    expired = copy.deepcopy(MOCK_TOKENS)
    expired["auth.globus.org"]["expires_at_seconds"] = int(time()) - 1
    token_storage.save_tokens(expired, NA_DEF["client_id"])


@pytest.fixture
def mock_input(monkeypatch):
    mock_input = mock.Mock()
    monkeypatch.setattr("globus_sdk.auth.oauth2_native_app_shortcut.input", mock_input)
    return mock_input


@pytest.fixture
def mock_safe_print(monkeypatch):
    mock_print = mock.Mock()
    monkeypatch.setattr("globus_sdk.auth.oauth2_native_app_shortcut.input", mock_print)
    return mock_print


def test_native_auth(
    mock_webbrowser, mock_local_server, mock_native_client, mock_save_tokens
):
    native_app_class, native_app_client = mock_native_client

    native_auth()

    native_app_class.assert_called_with(client_id=NA_DEF["client_id"])
    native_app_client.oauth2_start_flow.assert_called_with(
        requested_scopes=NA_DEF["requested_scopes"],
        redirect_uri=NA_DEF["redirect_uri"],
        refresh_tokens=NA_DEF["refresh_tokens"],
        prefill_named_grant=NA_DEF["prefill_named_grant"],
    )
    native_app_client.oauth2_get_authorize_url.assert_called_with(additional_params={})
    mock_local_server.assert_called_with(
        listen=(NA_DEF["server_hostname"], NA_DEF["server_port"])
    )
    assert native_app_client.oauth2_exchange_code_for_tokens.called
    assert not mock_save_tokens.called
    assert webbrowser.open.called


def test_invalid_option_raises_error(mock_native_client, mock_local_server):
    with pytest.raises(ValueError):
        native_auth(conquer_the_world=True)


def test_native_auth_saving_tokens(
    mock_save_tokens, mock_native_client, mock_local_server, temp_config
):
    native_auth(save_tokens=True)
    assert mock_save_tokens.called


def test_native_auth_loading_tokens(
    mock_native_client_simple, mock_local_server, saved_tokens
):
    native_auth()
    # assert tokens were loaded and a native flow was not started
    assert not mock_native_client_simple.called


def test_native_auth_force_login(
    mock_native_client_simple, mock_local_server, saved_tokens, mock_clear_tokens
):
    # Should disregard previously saved tokens
    native_auth(force_login=True)
    assert mock_native_client_simple.called
    assert mock_clear_tokens.called


def test_native_auth_requested_scope_check(
    mock_native_client_simple, mock_local_server, saved_tokens, mock_clear_tokens
):
    # Scopes here are different than what was saved, so this should
    # trigger an auth flow
    native_auth(requested_scopes=("foo",))
    assert mock_native_client_simple.called
    assert mock_clear_tokens.called


def test_native_auth_expired_token_check(
    mock_native_client_simple, mock_local_server, expired_saved_tokens
):
    native_auth()
    assert mock_native_client_simple.called


def test_native_auth_expired_token_no_check(
    mock_native_client_simple, mock_local_server, expired_saved_tokens
):
    native_auth(check_tokens_expired=False)
    assert not mock_native_client_simple.called


def test_native_auth_no_local_server(
    mock_local_server, mock_native_client, temp_config, mock_input, mock_safe_print
):
    native_app_class, native_app_client = mock_native_client

    native_auth(no_local_server=True)
    native_app_client.oauth2_start_flow.assert_called_with(
        requested_scopes=NA_DEF["requested_scopes"],
        redirect_uri=AUTH_CODE_REDIRECT,
        refresh_tokens=NA_DEF["refresh_tokens"],
        prefill_named_grant=NA_DEF["prefill_named_grant"],
    )
    assert native_app_class.called
    assert not mock_local_server.called
    assert mock_safe_print.called
    assert not mock_input.called


def test_native_auth_no_browser(
    mock_webbrowser, mock_local_server, mock_native_client_simple, mock_safe_print
):
    native_auth(no_browser=True)
    # Assert a native flow was not started
    assert mock_native_client_simple.called
    assert mock_local_server.called
    assert not webbrowser.open.called


def test_native_auth_custom_config_section(
    mock_native_client_simple, mock_local_server, temp_config
):
    my_section = "my_section"
    native_auth(config_section="my_section", save_tokens=True)
    assert my_section in globus_sdk.config.get_parser()._parser.sections()


def test_native_auth_ancillary_options(
    mock_webbrowser, mock_local_server, mock_native_client, mock_save_tokens
):
    """Options here don't change the control flow and should not affect
    one another. This test asserts they're present in expected places"""
    native_class, native_client = mock_native_client
    options = {
        "client_id": str(uuid.uuid4()),
        "redirect_uri": "http://example.com/login",
        "requested_scopes": ("myscope", "myotherscope"),
        "refresh_tokens": True,
        "prefill_named_grant": "Captain Hammer's Lenovo",
        "additional_auth_params": {"session_message": "hello!"},
        "server_hostname": "localhost",
        "server_port": 9999,
    }
    native_auth(**options)
    native_class.assert_called_with(client_id=options["client_id"])
    native_client.oauth2_start_flow.assert_called_with(
        requested_scopes=options["requested_scopes"],
        redirect_uri=options["redirect_uri"],
        refresh_tokens=options["refresh_tokens"],
        prefill_named_grant=options["prefill_named_grant"],
    )
    native_client.oauth2_get_authorize_url.assert_called_with(
        additional_params=options["additional_auth_params"]
    )
    mock_local_server.assert_called_with(
        listen=(options["server_hostname"], options["server_port"])
    )
