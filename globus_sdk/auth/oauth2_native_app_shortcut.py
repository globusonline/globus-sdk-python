import logging
import os
import webbrowser
from socket import gethostname

from six.moves import input

from globus_sdk.auth.client_types.native_client import NativeAppAuthClient
from globus_sdk.auth.oauth2_constants import DEFAULT_REQUESTED_SCOPES
from globus_sdk.exc import ConfigError
from globus_sdk.utils.local_server import is_remote_session, start_local_server
from globus_sdk.utils.safeio import safe_print
from globus_sdk.utils.token_storage import clear_tokens, load_tokens, save_tokens

logger = logging.getLogger(__name__)

AUTH_CODE_REDIRECT = "https://auth.globus.org/v2/web/auth-code"

NATIVE_AUTH_DEFAULTS = {
    "config_filename": os.path.expanduser("~/.globus-native-apps.cfg"),
    "config_section": None,  # Defaults to client_id if not set
    "client_id": "0af96eea-fec8-4d6e-aad2-c87feed8151c",
    "requested_scopes": DEFAULT_REQUESTED_SCOPES,
    "refresh_tokens": False,
    "prefill_named_grant": gethostname(),
    "additional_auth_params": {},
    "save_tokens": False,
    "check_tokens_expired": True,
    "force_login": False,
    "no_local_server": False,
    "no_browser": False,
    "server_hostname": "127.0.0.1",
    "server_port": 8890,
    "redirect_uri": "http://localhost:8890/",
}


def native_auth(**kwargs):
    """
    Provides a simple shortcut for doing a native auth flow for most use-cases
    by setting common defaults for frequently used fields. Although a default
    client id is provided, production apps should define their own at
    https://developers.globus.org. See `NativeAppAuthClient` for constructing
    a more fine-tuned native auth flow. Returns tokens organized by resource
    server.

    **Native App Parameters**
        ``client_id`` (*string*)
          Client App id registered at https://developers.globus.org. Defaults
          to a built-in one for testing.

        ``requested_scopes`` (*iterable* or *string*)
          The scopes on the token(s) being requested, as a space-separated
          string or iterable of strings. Defaults to ``openid profile email
          urn:globus:auth:scope:transfer.api.globus.org:all``

        ``redirect_uri`` (*string*)
          The page that users should be directed to after authenticating at
          the authorize URL. Defaults to
          'https://auth.globus.org/v2/web/auth-code', which displays the
          resulting ``auth_code`` for users to copy-paste back into your
          application (and thereby be passed back to the
          ``GlobusNativeAppFlowManager``)

        ``refresh_tokens`` (*bool*)
          When True, request refresh tokens in addition to access tokens

        ``prefill_named_grant`` (*string*)
          Optionally prefill the named grant label on the consent page

        ``additional_auth_params`` (*dict*)
          Set ``additional_parameters`` in
          NativeAppAuthClient.oauth2_get_authorize_url()

    **Login Parameters**
        ``save_tokens`` (*bool*)
          Save user tokens to disk and reload them on repeated calls.
          Defaults to False.

        ``check_tokens_expired`` (*bool*)
          Check if loaded access tokens have expired since the last login.
          You should set this to False if using Refresh Tokens.
          Defaults to True.

        ``force_login`` (*bool*)
          Do not attempt to load save tokens, and complete a new auth flow
          instead. Defaults to False.

        ``no_local_server`` (*bool*)
          Do not start a local server for fetching the auth_code. Setting
          this to false will require the user to copy paste a code into
          the console. Defaults to False.

        ``no_browser`` (*bool*)
          Do not automatically attempt to open a browser for the auth flow.
          Defaults to False.

        ``server_hostname`` (*string*)
          Hostname for the local server to use. No effect if
          ``no_local_server`` is set. MUST be specified in ``redirect_uri``.
          Defaults to 127.0.0.1.

        ``server_port`` (*string*)
          Port for the local server to use. No effect if ``no_local_server``
          is set. MUST be specified in ``redirect_uri``. Defaults to 8890.

    **Configfile Parameters**
        ``config_filename`` (*string*)
          Filename to use for reading and writing values.

        ``config_section`` (*string*)
          Section within the config file to store information (like tokens).

    **Examples**

    ``native_auth()``

    Or to save tokens: ``native_auth(save_tokens=True)``
    """
    unaccepted = [k for k in kwargs.keys() if k not in NATIVE_AUTH_DEFAULTS.keys()]
    if any(unaccepted):
        raise ValueError("Invalid args: {}".format(unaccepted))

    opts = {k: kwargs.get(k, v) for k, v in NATIVE_AUTH_DEFAULTS.items()}

    # Default to the auth-code page redirect if the user is copy-pasting
    if (
        opts["no_local_server"] is True
        and opts["redirect_uri"] == NATIVE_AUTH_DEFAULTS["redirect_uri"]
    ):
        opts["redirect_uri"] = AUTH_CODE_REDIRECT

    config_section = opts["config_section"] or opts["client_id"]

    if opts["force_login"] is False:
        try:
            return load_tokens(
                config_section, opts["requested_scopes"], opts["check_tokens_expired"]
            )
        except ConfigError as ce:
            logger.debug(
                "Loading Tokens Failed, doing auth flow instead. "
                "Error: {}".format(ce)
            )

    # Clear previous tokens to ensure no previously saved scopes remain.
    clear_tokens(config_section=config_section, client_id=opts["client_id"])

    client = NativeAppAuthClient(client_id=opts["client_id"])
    client.oauth2_start_flow(
        requested_scopes=opts["requested_scopes"],
        redirect_uri=opts["redirect_uri"],
        refresh_tokens=opts["refresh_tokens"],
        prefill_named_grant=opts["prefill_named_grant"],
    )
    url = client.oauth2_get_authorize_url(
        additional_params=opts["additional_auth_params"]
    )

    if opts["no_local_server"] is False:
        server_address = (opts["server_hostname"], opts["server_port"])
        with start_local_server(listen=server_address) as server:
            _prompt_login(url, opts["no_browser"])
            auth_code = server.wait_for_code()
    else:
        _prompt_login(url, opts["no_browser"])
        safe_print("Enter the resulting Authorization Code here: ", end="")
        auth_code = input()

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)
    tokens_by_resource_server = token_response.by_resource_server
    if opts["save_tokens"] is True:
        save_tokens(tokens_by_resource_server, config_section)
    # return a set of tokens, organized by resource server name

    return tokens_by_resource_server


def _prompt_login(url, no_browser):
    if no_browser is False and not is_remote_session():
        webbrowser.open(url, new=1)
    else:
        safe_print("Please paste the following URL in a browser: " "\n{}".format(url))
