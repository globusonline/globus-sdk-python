import logging
import time

from globus_sdk.auth.client_types.native_client import NativeAppAuthClient
from globus_sdk.config import get_parser
from globus_sdk.exc import ConfigError, LoadedTokensExpired, RequestedScopesMismatch

TOKEN_KEYS = [
    "scope",
    "access_token",
    "refresh_token",
    "token_type",
    "expires_at_seconds",
    "resource_server",
]
REQUIRED_KEYS = ["scope", "access_token", "expires_at_seconds", "resource_server"]
CONFIG_TOKEN_GROUPS = "token_groups"

logger = logging.getLogger(__name__)


def save_tokens(tokens, config_section=None):
    """
    Save a dict of tokens in config_section, for the current configfile.
    Tokens should be formatted like the following:
    {
        "auth.globus.org": {
            "scope": "profile openid email",
            "access_token": "<token>",
            "refresh_token": None,
            "token_type": "Bearer",
            "expires_at_seconds": 1539984535,
            "resource_server": "auth.globus.org"
        }, ...
    }
    """
    config = get_parser()

    cfg_tokens = _serialize_token_groups(tokens)
    for key, value in cfg_tokens.items():
        config.set(key, value, section=config_section)


def load_tokens(config_section=None, requested_scopes=(), check_expired=True):
    """
    Load Tokens from a config section in the configfile. If requested_scopes
    is given, it will match against the loaded scopes and raise a
    RequestedScopesMismatch exception if they differ from one another.

    check_expired will check the expires_at_seconds number against the time
    the user last logged in, and raise LoadedTokensExpired if it is greater.
    check_expired should be set to false if you want to use refresh tokens.

    Returns tokens in a similar format to token_response.by_resource_server:
    {
        "auth.globus.org": {
            "scope": "profile openid email",
            "access_token": "<token>",
            "refresh_token": None,
            "token_type": "Bearer",
            "expires_at_seconds": 1539984535,
            "resource_server": "auth.globus.org"
        }, ...
    }
    """

    config = get_parser()
    try:
        cfg_tokens = config.get_section(config_section)
        loaded_tokens = _deserialize_token_groups(cfg_tokens)
    except Exception:
        raise ConfigError("Error loading tokens from: {}".format(config_section))

    for tok_set in loaded_tokens.values():
        missing = [mk for mk in REQUIRED_KEYS if not tok_set.get(mk)]
        if any(missing):
            raise ConfigError("Missing {} from loaded tokens".format(missing))

    if requested_scopes:
        scope_lists = [t["scope"].split() for t in loaded_tokens.values()]
        loaded_scopes = {s for slist in scope_lists for s in slist}
        if loaded_scopes.difference(set(requested_scopes)):
            raise RequestedScopesMismatch(
                "Requested Scopes differ from loaded scopes. Requested: "
                "{}, Loaded: {}".format(requested_scopes, list(loaded_scopes))
            )

    if check_expired is True:
        expired = [
            time.time() >= t["expires_at_seconds"] for t in loaded_tokens.values()
        ]
        if any(expired):
            raise LoadedTokensExpired()

    return loaded_tokens


def clear_tokens(config_section=None, client_id=None):
    """Revokes and deletes tokens saved to disk. ``config_section`` is the
    section where the tokens are stored, ``client_id`` must be a valid Globus
    App. Returns True if tokens were revoked (or expired) and deleted, false
    otherwise. Raises globus_sdk.exc.AuthAPIError if tokens are live and
    client_id is invalid.
    """
    tokens = []
    try:
        naac = NativeAppAuthClient(client_id)
        tokens = load_tokens(config_section=config_section, check_expired=True)
        for tok_set in tokens.values():
            logger.debug("Revoking: {}".format(tok_set["resource_server"]))
            naac.oauth2_revoke_token(tok_set["access_token"])
    except LoadedTokensExpired:
        # If they expired, no need to revoke but fetch again for deletion
        tokens = load_tokens(config_section=config_section, check_expired=False)
    except ConfigError as ce:
        logger.debug(ce)

    if not tokens:
        return False

    cfg_tsets = _serialize_token_groups(tokens)
    config = get_parser()
    for cfg_token_name in cfg_tsets.keys():
        config.remove(cfg_token_name, section=config_section)
    config.remove(CONFIG_TOKEN_GROUPS, section=config_section)
    return True


def _serialize_token_groups(tokens):
    """
    Take a dict of tokens organized by resource server and return a dict
    that can be easily saved to the config file.

    Resource servers containing '.' in their name will automatically be
    converted to '_' (auth.globus.org == auth_globus_org). This is only for
    cosmetic reasons. A resource server named "foo=;# = !@#$%^&*()" will have
    funky looking config keys, but saving/loading will behave normally.

    Int values are converted to string, None values are converted to empty
    string. *No other types are checked*.

    `tokens` should be formatted:
    {
        "auth.globus.org": {
            "scope": "profile openid email",
            "access_token": "<token>",
            "refresh_token": None,
            "token_type": "Bearer",
            "expires_at_seconds": 1539984535,
            "resource_server": "auth.globus.org"
        }, ...
    }
    Returns a flat dict of tokens prefixed by resource server.
    {
        "auth_globus_org_scope": "profile openid email",
        "auth_globus_org_access_token": "<token>",
        "auth_globus_org_refresh_token": "",
        "auth_globus_org_token_type": "Bearer",
        "auth_globus_org_expires_at_seconds": "1540051101",
        "auth_globus_org_resource_server": "auth.globus.org",
        "token_groups": "auth_globus_org"
    }"""
    serialized_items = {}
    token_groups = []
    for token_set in tokens.values():
        token_groups.append(_serialize_token(token_set["resource_server"]))
        for key, value in token_set.items():
            key_name = _serialize_token(token_set["resource_server"], key)
            if isinstance(value, int):
                value = str(value)
            if value is None:
                value = ""
            serialized_items[key_name] = value

    serialized_items[CONFIG_TOKEN_GROUPS] = ",".join(token_groups)
    return serialized_items


def _deserialize_token_groups(config_items):
    """
    Takes a dict from a config section and returns a dict of tokens by
    resource server. `config_items` is a raw dict of config options returned
    from get_parser().get_section().

    Returns tokens in the format:
    {
        "auth.globus.org": {
            "scope": "profile openid email",
            "access_token": "<token>",
            "refresh_token": None,
            "token_type": "Bearer",
            "expires_at_seconds": 1539984535,
            "resource_server": "auth.globus.org"
        }, ...
    }
    """
    token_groups = {}

    tsets = config_items.get(CONFIG_TOKEN_GROUPS)
    config_token_groups = tsets.split(",")
    for group in config_token_groups:
        tset = {k: config_items.get(_deserialize_token(group, k)) for k in TOKEN_KEYS}
        tset["expires_at_seconds"] = int(tset["expires_at_seconds"])
        # Config loaded 'null' values will be an empty string. Set these to
        # None for consistency
        tset = {k: v if v else None for k, v in tset.items()}
        token_groups[tset["resource_server"]] = tset

    return token_groups


def _deserialize_token(grouping, token):
    return "{}{}".format(grouping, token)


def _serialize_token(resource_server, token=""):
    return "{}_{}".format(resource_server.replace(".", "_"), token)
