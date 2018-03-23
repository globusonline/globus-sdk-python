import logging

from globus_sdk.authorizers.renewing import RenewingAuthorizer


logger = logging.getLogger(__name__)


class RefreshTokenAuthorizer(RenewingAuthorizer):
    """
    Implements Authorization using a Refresh Token to periodically fetch
    renewed Access Tokens. It may be initialized with an Access Token, or it
    will fetch one the first time that ``set_authorization_header()`` is
    called.

    Example usage looks something like this:

    >>> import globus_sdk
    >>> auth_client = globus_sdk.AuthClient(client_id=..., client_secret=...)
    >>> # do some flow to get a refresh token from auth_client
    >>> rt_authorizer = globus_sdk.RefreshTokenAuthorizer(
    >>>     refresh_token, auth_client)
    >>> # create a new client
    >>> transfer_client = globus_sdk.TransferClient(authorizer=rt_authorizer)

    anything that inherits from :class:`BaseClient <globus_sdk.BaseClient>`, so
    at least ``TransferClient`` and ``AuthClient`` will automatically handle
    usage of the ``RefreshTokenAuthorizer``.

    **Parameters**

        ``refresh_token`` (*string*)
          Refresh Token for Globus Auth

        ``auth_client`` (:class:`AuthClient <globus_sdk.AuthClient>`)
          ``AuthClient`` capable of using the ``refresh_token``

        ``access_token`` (*string*)
          Initial Access Token to use, only used if ``expires_at`` is also set

        ``expires_at`` (*int*)
          Expiration time for the starting ``access_token`` expressed as a
          POSIX timestamp (i.e. seconds since the epoch)

        ``on_refresh`` (*callable*)
        Will be called as fn(token_data) any time this authorizer
        fetches a new access_token
    """
    def __init__(self, refresh_token, auth_client,
                 access_token=None, expires_at=None, on_refresh=None):
        logger.info((
            "Setting up RefreshTokenAuthorizer with auth_client = "
            "instance: {0}".format(id(auth_client))))

        # required for _get_token_data
        self.refresh_token = refresh_token
        self.auth_client = auth_client

        super(RefreshTokenAuthorizer, self).__init__(
            access_token, expires_at, on_refresh)

    def _get_token_response(self):
        """
        Make a refresh token grant
        """
        return self.auth_client.oauth2_refresh_token(self.refresh_token)

    def _extract_token_data(self, res):
        """
        Get the tokens .by_resource_server,
        Ensure that only one token was gotten, and return that token.
        """
        token_data = res.by_resource_server.values()
        if len(token_data) != 1:
            raise ValueError(
                "Attempting refresh for refresh token authorizer "
                "didn't return exactly one token. Possible service error.")

        return next(iter(token_data))
