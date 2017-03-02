from __future__ import print_function

import six
import collections
import logging

from globus_sdk.base import BaseClient, safe_stringify
from globus_sdk.authorizers import NullAuthorizer
from globus_sdk.auth.token_response import OAuthTokenResponse

logger = logging.getLogger(__name__)


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

    **Examples**

    Initializing an ``AuthClient`` to authenticate a user making calls to the
    Globus Auth service with an access token takes the form

    >>> from globus_sdk import AuthClient, AccessTokenAuthorizer
    >>> ac = AuthClient(authorizer=AccessTokenAuthorizer('<token_string>'))

    You can, of course, use other kinds of Authorizers (notably the
    ``RefreshTokenAuthorizer``).
    """
    def __init__(self, client_id=None, authorizer=None, **kwargs):
        self.client_id = client_id

        # an AuthClient may contain a GlobusOAuth2FlowManager in order to
        # encapsulate the functionality of various different types of flow
        # managers
        self.current_oauth2_flow_manager = None

        BaseClient.__init__(self, "auth", authorizer=authorizer, **kwargs)

    def get_identities(self, usernames=None, ids=None,
                       provision=False, **params):
        r"""
        GET /v2/api/identities

        Given ``usernames=<U>`` or (exclusive) ``ids=<I>`` as keyword
        arguments, looks up identity information for the set of identities
        provided.
        ``<U>`` and ``<I>`` in this case are comma-delimited strings listing
        multiple Identity Usernames or Identity IDs, or iterables of strings,
        each of which is an Identity Username or Identity ID.

        If Globus Auth's identity auto-provisioning behavior is desired,
        ``provision=True`` may be specified.

        Available with any authentication/client type.

        **Examples**

        >>> ac = globus_sdk.AuthClient(...)
        >>> # by IDs
        >>> r = ac.get_identities(ids="46bd0f56-e24f-11e5-a510-131bef46955c")
        >>> r.data
        {u'identities': [{u'email': None,
           u'id': u'46bd0f56-e24f-11e5-a510-131bef46955c',
           u'identity_provider': u'7daddf46-70c5-45ee-9f0f-7244fe7c8707',
           u'name': None,
           u'organization': None,
           u'status': u'unused',
           u'username': u'globus@globus.org'}]}
        >>> ac.get_identities(
        >>>     ids=",".join(
        >>>         ("46bd0f56-e24f-11e5-a510-131bef46955c",
        >>>          "168edc3d-c6ba-478c-9cf8-541ff5ebdc1c"))
        ...
        >>> # or by usernames
        >>> ac.get_identities(usernames='globus@globus.org')
        ...
        >>> ac.get_identities(
        >>>     usernames='globus@globus.org,auth@globus.org')
        ...

        You could also use iterables:

        >>> ac.get_identities(
        >>>     usernames=['globus@globus.org', 'auth@globus.org'])
        ...
        >>> ac.get_identities(
        >>>     ids=["46bd0f56-e24f-11e5-a510-131bef46955c",
        >>>          "168edc3d-c6ba-478c-9cf8-541ff5ebdc1c"])
        ...


        **External Documentation**

        See
        `Identities Resources \
        <https://docs.globus.org/api/auth/reference/
        #v2_api_identities_resources>`_
        in the API documentation for details.
        """
        def _convert_listarg(val):
            if (isinstance(val, collections.Iterable) and
                    not isinstance(val, six.string_types)):
                return ','.join(safe_stringify(x) for x in val)
            else:
                return safe_stringify(val)

        self.logger.info('Looking up Globus Auth Identities')

        # if either of these params has a truthy value, stringify it safely,
        # letting us consume args whose `__str__` methods produce "the right
        # thing"
        # most notably, lets `ids` take a single UUID object safely
        if usernames:
            params['usernames'] = _convert_listarg(usernames)
            params['provision'] = ('false' if str(provision).lower() == 'false'
                                   else 'true')
        if ids:
            params['ids'] = _convert_listarg(ids)

        self.logger.debug('params={}'.format(params))

        if 'usernames' in params and 'ids' in params:
            self.logger.warn(('get_identities call with both usernames and '
                              'identities set! Expected to result in errors'))

        return self.get("/v2/api/identities", params=params)

    def oauth2_get_authorize_url(self, additional_params=None):
        """
        Get the authorization URL to which users should be sent.
        This method may only be called after an ``oauth2_start_flow_*`` method
        has been called on this ``AuthClient``.

        **Parameters**

            ``additional_params`` (*dict*)
              A ``dict`` or ``None``, which specifies additional query
              parameters to include in the authorize URL. Primarily for
              internal use

        :rtype: ``string``
        """
        if not self.current_oauth2_flow_manager:
            self.logger.error(('OutOfOrderOperations('
                               'get_authorize_url before start_flow)'))
            raise ValueError(
                ('Cannot get authorize URL until starting an OAuth2 flow. '
                 'Call one of the oauth2_start_flow_*() methods on this '
                 'AuthClient to resolve'))
        auth_url = self.current_oauth2_flow_manager.get_authorize_url(
            additional_params=additional_params)
        self.logger.info('Got authorization URL: {}'.format(auth_url))
        return auth_url

    def oauth2_exchange_code_for_tokens(self, auth_code):
        """
        Exchange an authorization code for a token or tokens.

        :rtype: :class:`OAuthTokenResponse \
        <globus_sdk.auth.token_response.OAuthTokenResponse>`

        ``auth_code``
          An auth code typically obtained by sending the user to the authorize
          URL. The code is a very short-lived credential which this method is
          exchanging for tokens. Tokens are the credentials used to
          authenticate against Globus APIs.
        """
        self.logger.info(('Final Step of 3-legged OAuth2 Flows: '
                          'Exchanging authorization code for token(s)'))
        if not self.current_oauth2_flow_manager:
            self.logger.error(('OutOfOrderOperations('
                               'exchange_code before start_flow)'))
            raise ValueError(
                ('Cannot exchange auth code until starting an OAuth2 flow. '
                 'Call one of the oauth2_start_flow_*() methods on this '
                 'AuthClient to resolve'))

        return self.current_oauth2_flow_manager.exchange_code_for_tokens(
            auth_code)

    def oauth2_refresh_token(self, refresh_token, additional_params=None):
        r"""
        Exchange a refresh token for a :class:`OAuthTokenResponse
        <globus_sdk.auth.token_response.OAuthTokenResponse>`, containing
        an access token.

        Does a token call of the form

        .. code-block:: none

            refresh_token=<refresh_token>
            grant_type=refresh_token

        plus any additional parameters you may specify.

        ``refresh_token``
          A raw Refresh Token string

        ``additional_params``
          A dict of extra params to encode in the refresh call.
        """
        self.logger.info(('Executing token refresh; '
                          'typically requires client credentials'))
        form_data = {'refresh_token': refresh_token,
                     'grant_type': 'refresh_token'}

        if additional_params:
            form_data.update(additional_params)
        return self.oauth2_token(form_data)

    def oauth2_revoke_token(self, token, additional_params=None):
        """
        Revoke a token. It can be an Access Token or a Refresh token.

        This call should be used to revoke tokens issued to your client,
        rendering them inert and not further usable. Typically, this is
        incorporated into "logout" functionality, but it should also be used if
        the client detects that its tokens are in an unsafe location (e.x.
        found in a world-readable logfile).

        You can check the "active" status of the token after revocation if you
        want to confirm that it was revoked.

        **Parameters**

            ``token`` (*string*)
              The token which should be revoked

            ``additional_params`` (*dict*)
              A ``dict`` or ``None``, which specifies additional
              parameters to include in the revocation body, which can help
              speed the revocation process. Primarily for internal use

        **Examples**

        >>> from globus_sdk import ConfidentialAppAuthClient
        >>> ac = ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)
        >>> ac.oauth2_revoke_token('<token_string>')
        """
        self.logger.info('Revoking token')
        body = {'token': token}

        # if this client has no way of authenticating itself but
        # it does have a client_id, we'll send that in the request
        no_authentication = (self.authorizer is None or
                             isinstance(self.authorizer, NullAuthorizer))
        if no_authentication and self.client_id:
            self.logger.debug('Revoking token with unauthenticated client')
            body.update({'client_id': self.client_id})

        if additional_params:
            body.update(additional_params)
        return self.post('/v2/oauth2/token/revoke', text_body=body)

    def oauth2_token(self, form_data, response_class=OAuthTokenResponse):
        """
        This is the generic form of calling the OAuth2 Token endpoint.
        It takes ``form_data``, a dict which will be encoded in a form POST
        body on the request.

        Generally, users of the SDK should not call this method unless they are
        implementing OAuth2 flows.

        **Parameters**

            ``response_type``
              Defaults to :class:`OAuthTokenResponse \
              <globus_sdk.auth.token_response.OAuthTokenResponse>`. This is
              used by calls to the oauth2_token endpoint which need to
              specialize their responses. For example,
              :meth:`oauth2_get_dependent_tokens \
              <globus_sdk.ConfidentialAppAuthClient.oauth2_get_dependent_tokens>`
              requires a specialize response class to handle the dramatically
              different nature of the Dependent Token Grant response

        :rtype: ``response_class``
        """
        self.logger.info('Fetching new token from Globus Auth')
        # use the fact that requests implicitly encodes the `data` parameter as
        # a form POST
        return self.post(
            '/v2/oauth2/token', response_class=response_class,
            text_body=form_data)

    def oauth2_userinfo(self):
        """
        Call the Userinfo endpoint of Globus Auth.
        Userinfo is specified as part of the OpenID Connect (OIDC) standard,
        and Globus Auth's Userinfo is OIDC-compliant.

        The exact data returned will depend upon the set of OIDC-related scopes
        which were used to acquire the token being used for this call. For
        details, see the **External Documentation** below.

        **Examples**

        >>> ac = AuthClient(...)
        >>> info = ac.oauth2_userinfo()
        >>> print('Effective Identity "{}" has Full Name "{}" and Email "{}"'
        >>>       .format(info["sub"], info["name"], info["email"]))

        **External Documentation**

        See
        `Userinfo \
        <https://docs.globus.org/api/auth/reference/
        #get_or_post_v2_oauth2_userinfo_resource>`_
        in the API documentation for details.
        """
        self.logger.info('Looking up OIDC-style Userinfo from Globus Auth')
        return self.get('/v2/oauth2/userinfo')
