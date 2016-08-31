import uuid
import hashlib
import base64
from six.moves.urllib.parse import urlencode

from globus_sdk.base import slash_join
from globus_sdk.auth.oauth_flow_manager import GlobusOAuthFlowManager
from globus_sdk.auth.token_response import (
    GlobusOAuthTokenResponse)


def make_native_app_challenge(verifier=None):
    """
    Produce a challenge and verifier for the Native App flow.
    The verifier is an unhashed secret, and the challenge is a hashed version
    of it. The challenge is sent at the start of the flow, and the secret is
    sent at the end, proving that the same client that started the flow is
    continuing it.
    Hashing is always done with simple SHA256
    """
    # unless provided, the "secret" is just a UUID4
    code_verifier = verifier or str(uuid.uuid4())
    # hash it, pull out a digest
    hashed_verifier = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    # urlsafe base64 encode that hash
    code_challenge = base64.urlsafe_b64encode(hashed_verifier).decode('utf-8')

    # return the verifier and the encoded hash
    return code_verifier, code_challenge


class GlobusNativeAppFlowManager(GlobusOAuthFlowManager):
    """
    This is the OAuth flow designated for use by clients wishing to
    authenticate users in the absence of a Client Secret. Because these
    applications run "natively" in the user's environment, they cannot
    protect a secret.
    Instead, a temporary secret is generated solely for this authentication
    attempt.

    :param auth_client: The ``AuthClient`` object on which this flow is
                        based. Used to extract default values for the flow, and
                        also to make POST calls to the Auth service.
    :param client_id: The Client ID to use for this flow.
                      Defaults to the ``auth_client.client_id``, which can
                      be set by
                      :meth:`~globus_sdk.AuthClient.set_client_id` or by
                      :meth:`~globus_sdk.AuthClient.set_auth_basic`
    :param requested_scopes: The scopes on the token(s) at the end of the
                             OAuth2 flow. Defaults to a set of commonly
                             desired scopes for Globus.
    :param redirect_uri: A page that users should be directed to after
                         authenticating at the authorize URL. Defaults to
                         'https://auth.globus.org/v2/web/auth-code', which
                         displays the resulting ``auth_code`` for users to
                         copy-paste back into your application (and thereby
                         be passed back to the ``GlobusNativeAppFlowManager``)
    :param state: The state parameter for 3-legged OAuth2 flows. Typically
                  this is not meaningful in the Native App Grant flow, but
                  you may have a specialized use case for it. The
                  ``redirect_uri`` page will have this included in a query
                  parameter, so you can use it to pass information to that
                  page. It defaults to the string '_default'
    :param verifier: A secret string used for the Native App flow, known
                     only to this instance of the client. By default, one
                     will be generated and saved on this instance of the flow
    :param refresh_token: A ``bool``. When True, request a refresh token
                          in addition to an access token.

    The returned URL string is encoded to be suitable to display to users
    in a link or to copy into their browser. Users will be redirected
    either to your provided ``redirect_uri`` or to the default location,
    with the ``auth_code`` embedded in a query parameter.
    """

    def __init__(self, auth_client, client_id=None, requested_scopes=None,
                 redirect_uri=None, state='_default', verifier=None,
                 refresh_token=False):
        self.auth_client = auth_client

        # default to auth_client.client_id, then check for validity
        self.client_id = client_id or auth_client.client_id
        if not self.client_id:
            raise ValueError(
                'Invalid value for client_id. Got "{0}"'.format(client_id))

        # default to the default requested scopes
        self.requested_scopes = requested_scopes or (
                'openid profile email '
                'urn:globus:auth:scope:transfer.api.globus.org:all')

        # default to `/v2/web/auth-code` on whatever environment we're looking
        # at -- most typically it will be `https://auth.globus.org/`
        self.redirect_uri = redirect_uri or (
            slash_join(auth_client.base_url, '/v2/web/auth-code'))

        # make a challenge and secret to keep
        # if the verifier is provided, it will just be passed back to us, and
        # if not, one will be generated
        self.verifier, self.challenge = make_native_app_challenge(verifier)

        # store the remaining parameters directly, with no transformation
        self.refresh_token = refresh_token
        self.state = state

    def get_authorize_url(self):
        """
        Start a Native App flow by getting the authorization URL to which users
        should be sent.

        :rtype: ``string``

        The returned URL string is encoded to be suitable to display to users
        in a link or to copy into their browser. Users will be redirected
        either to your provided ``redirect_uri`` or to the default location,
        with the ``auth_code`` embedded in a query parameter.
        """
        authorize_base_url = slash_join(self.auth_client.base_url,
                                        '/v2/oauth2/authorize')

        params = urlencode(
            {'client_id': self.client_id,
             'redirect_uri': self.redirect_uri,
             'scope': self.requested_scopes,
             'state': self.state,
             'response_type': 'code',
             'code_challenge': self.challenge,
             'code_challenge_method': 'S256',
             'access_type': (self.refresh_token and 'offline') or 'online'
             })
        return '{0}?{1}'.format(authorize_base_url, params)

    def exchange_code_for_tokens(self, auth_code):
        """
        The second step of the Native App flow, exchange an authorization code
        for a token (or tokens if a refresh token will be included).

        :rtype: :class:`GlobusResponse <globus_sdk.response.GlobusResponse>`
        """
        # use the fact that requests implicitly encodes the `data` parameter as
        # a form POST
        return self.auth_client.post(
            '/v2/oauth2/token', response_class=GlobusOAuthTokenResponse,
            text_body={'client_id': self.client_id,
                       'grant_type': 'authorization_code',
                       'code': auth_code.encode('utf-8'),
                       'code_verifier': self.verifier,
                       'redirect_uri': self.redirect_uri},
            no_auth_header=True
            )
