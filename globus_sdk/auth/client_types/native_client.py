import logging
from globus_sdk.authorizers import NullAuthorizer
from globus_sdk.auth.client_types.base import AuthClient
from globus_sdk.auth.oauth2_native_app import GlobusNativeAppFlowManager

logger = logging.getLogger(__name__)


class NativeAppAuthClient(AuthClient):
    """
    This type of ``AuthClient`` is used to represent a Native App's
    communications with Globus Auth.
    It requires a Client ID, and cannot take an ``authorizer``.

    Native Apps are applications, like the Globus CLI, which are run
    client-side and therefore cannot keep secrets. Unable to possess client
    credentials, several Globus Auth interactions have to be specialized to
    accommodate the absence of a secret.

    Any keyword arguments given are passed through to the ``AuthClient``
    constructor.
    """
    # don't allow any authorizer to be used on a native app client
    # it can't authorize it's calls, and shouldn't try to
    allowed_authorizer_types = [NullAuthorizer]

    def __init__(self, client_id, **kwargs):
        if "authorizer" in kwargs:
            logger.error('ArgumentError(NativeAppClient.authorizer)')
            raise ValueError(
                "Cannot give a NativeAppAuthClient an authorizer")

        AuthClient.__init__(
            self, client_id=client_id, authorizer=NullAuthorizer(), **kwargs)
        self.logger.info('Finished initializing client, client_id={}'
                         .format(client_id))

    def oauth2_start_flow_native_app(self, *args, **kwargs):
        """
        Deprecated passthrough method for getting at ``self.oauth2_start_flow``
        """
        self.logger.warn(("Using oauth2_start_flow_native_app() is "
                          "deprecated. Recommend upgrade to "
                          "oauth2_start_flow()"))
        return self.oauth2_start_flow(*args, **kwargs)

    def oauth2_start_flow(
            self, requested_scopes=None, redirect_uri=None,
            state='_default', verifier=None, refresh_tokens=False,
            prefill_named_grant=None):
        """
        Starts a Native App OAuth2 flow by instantiating a
        :class:`GlobusNativeAppFlowManager
        <globus_sdk.auth.GlobusNativeAppFlowManager>`

        All of the parameters to this method are passed to that class's
        initializer verbatim.

        #notthreadsafe
        """
        self.logger.info('Starting Native App Grant Flow')
        self.current_oauth2_flow_manager = GlobusNativeAppFlowManager(
            self, requested_scopes=requested_scopes,
            redirect_uri=redirect_uri, state=state, verifier=verifier,
            refresh_tokens=refresh_tokens,
            prefill_named_grant=prefill_named_grant)
        return self.current_oauth2_flow_manager

    def oauth2_refresh_token(self, refresh_token):
        """
        ``NativeAppAuthClient`` specializes the refresh token grant to include
        its client ID as a parameter in the POST body.
        It needs this specialization because it cannot authenticate the refresh
        grant call with client credentials, as is normal.
        """
        self.logger.info('Executing token refresh without client credentials')
        form_data = {'refresh_token': refresh_token,
                     'grant_type': 'refresh_token',
                     'client_id': self.client_id}

        return self.oauth2_token(form_data)
