from __future__ import print_function

from six.moves.urllib.parse import urlencode

from globus_sdk import config
from globus_sdk.base import BaseClient, merge_params
from globus_sdk.auth.oauth2_native_app import GlobusNativeAppFlowManager


class AuthClient(BaseClient):
    """
    Client for the
    `Globus Auth API <https://docs.globus.org/api/auth/>`_

    This class provides helper methods for most common resources in the
    Auth API, and the common low-level interface from
    :class:`BaseClient <globus_sdk.base.BaseClient>` of ``get``, ``put``,
    ``post``, and ``delete`` methods, which can be used to access any API
    resource.

    There are generally two types of resources, distinguished by the type
    of authentication which they use. Resources available to end users of
    Globus are authenticated with a Globus Auth Token
    ("Authentication: Bearer ..."), while resources available to OAuth
    Clients are authenticated using Basic Auth with the Client's ID and
    Secret.
    Some resources may be available with either authentication type.
    """
    def __init__(self, environment=config.get_default_environ(), token=None,
                 app_name=None, client_id=None):
        BaseClient.__init__(self, "auth", environment, token=token,
                            app_name=app_name)
        self.client_id = client_id

        # an AuthClient may contain a GlobusOAuth2FlowManager in order to
        # encapsulate the functionality of various different types of flow
        # managers
        self.current_oauth2_flow_manager = None

    def config_load_token(self):
        return config.get_auth_token(self.environment)

    def set_client_id(self, client_id):
        """
        Set the Globus Auth Client ID on this ``AuthClient``.
        This is used as a default in several methods that accept a
        ``client_id`` parameter on the ``AuthClient``.
        """
        self.client_id = client_id

    def set_auth_basic(self, username, password):
        """
        Override the ``BaseClient`` version of this call to also set the Client
        ID.
        """
        self.set_client_id(username)
        BaseClient.set_auth_basic(self, username, password)

    def get_identities(self, **params):
        """
        GET /v2/api/identities

        Given ``usernames=<U>`` or (exclusive) ``identity_ids=<I>`` as keyword
        arguments, looks up identity information for the set of identities
        provided.
        ``<U>`` and ``<I>`` in this case are comma-delimited strings listing
        multiple Identity Usernames or Identity IDs.

        Available with either authentication type.

        See
        `Identities Resources \
        <https://docs.globus.org/api/auth/reference/\
        #v2_api_identities_resources>`_
        in the API documentation for details.
        """
        return self.get("/v2/api/identities", params=params)

    def token_introspect(self, token, **kw):
        """
        POST /v2/oauth2/token/introspect

        Get information about a Globus Auth token.

        Requires Basic Auth using Oauth Client credentials.

        See
        `Token Introspection \
        <https://docs.globus.org/api/auth/reference/\
        #token_introspection_post_v2_oauth2_token_introspect>`_
        in the API documentation for details.
        """
        merge_params(kw, token=token)
        return self.post("/v2/oauth2/token/introspect",
                         text_body=urlencode(kw))

    def oauth2_native_app_start_flow(
            self, client_id=None, requested_scopes=None, redirect_uri=None,
            state='_default', verifier=None, refresh_tokens=False):
        """
        Starts a Native App OAuth2 flow by instantiating a
        :class:`GlobusNativeAppFlowManager
        <globus_sdk.auth.GlobusNativeAppFlowManager>`

        All of the parameters to this method are passed to that class's
        initializer verbatim.

        #notthreadsafe
        """
        self.current_oauth2_flow_manager = GlobusNativeAppFlowManager(
            self, client_id=client_id, requested_scopes=requested_scopes,
            redirect_uri=redirect_uri, state=state, verifier=verifier,
            refresh_tokens=refresh_tokens)
        return self.current_oauth2_flow_manager

    def oauth2_get_authorize_url(self):
        """
        Get the authorization URL to which users should be sent.
        This method may only be called after an ``oauth2_*_start_flow`` method
        has been called on this ``AuthClient``.

        :rtype: ``string``
        """
        if not self.current_oauth2_flow_manager:
            raise ValueError(
                ('Cannot get authorize URL until starting an OAuth2 flow. '
                 'Call one of the oauth2_*_start_flow() methods on this '
                 'AuthClient to resolve'))
        return self.current_oauth2_flow_manager.get_authorize_url()

    def oauth2_exchange_code_for_tokens(self, auth_code):
        """
        Exchange an authorization code for a token or tokens.

        :rtype: :class:`GlobusOAuthTokenResponse \
        <globus_sdk.auth.token_response.GlobusOAuthTokenResponse>`

        :param auth_code: An auth code typically obtained by sending the user
                          to the authorize URL. This is a very short-lived
                          credential which this method is exchanging for
                          tokens, which are longer-lived.
        """
        if not self.current_oauth2_flow_manager:
            raise ValueError(
                ('Cannot exchange auth code until starting an OAuth2 flow. '
                 'Call one of the oauth2_*_start_flow() methods on this '
                 'AuthClient to resolve'))

        return self.current_oauth2_flow_manager.exchange_code_for_tokens(
            auth_code)
