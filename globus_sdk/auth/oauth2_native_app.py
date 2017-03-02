import logging
import uuid
import hashlib
import base64
from six.moves.urllib.parse import urlencode

from globus_sdk.base import slash_join
from globus_sdk.auth.oauth2_constants import DEFAULT_REQUESTED_SCOPES
from globus_sdk.auth.oauth_flow_manager import GlobusOAuthFlowManager

logger = logging.getLogger(__name__)


def make_native_app_challenge(verifier=None):
    """
    Produce a challenge and verifier for the Native App flow.
    The verifier is an unhashed secret, and the challenge is a hashed version
    of it. The challenge is sent at the start of the flow, and the secret is
    sent at the end, proving that the same client that started the flow is
    continuing it.
    Hashing is always done with simple SHA256
    """
    if not verifier:
        logger.info(('Autogenerating verifier secret. On low-entropy systems '
                     'this may be insecure'))

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

    **Parameters**

        ``auth_client`` (*AuthClient*)
          The ``NativeAppAuthClient`` object on which this flow is based. It is
          used to extract default values for the flow, and also to make calls
          to the Auth service. This SHOULD be a ``NativeAppAuthClient``

        ``requested_scopes`` (*string*)
          The scopes on the token(s) being requested, as a space-separated
          string. Defaults to ``openid profile email
          urn:globus:auth:scope:transfer.api.globus.org:all``

        ``redirect_uri`` (*string*)
          The page that users should be directed to after authenticating at the
          authorize URL. Defaults to
          'https://auth.globus.org/v2/web/auth-code', which displays the
          resulting ``auth_code`` for users to copy-paste back into your
          application (and thereby be passed back to the
          ``GlobusNativeAppFlowManager``)

        ``state`` (*string*)
          Typically is not meaningful in the Native App Grant flow, but you may
          have a specialized use case for it. The ``redirect_uri`` page will
          have this included in a query parameter, so you can use it to pass
          information to that page. It defaults to the string '_default'

        ``verifier`` (*string*)
          A secret used for the Native App flow. It will by default be a
          freshly generated random string, known only to this
          ``GlobusNativeAppFlowManager`` instance

        ``refresh_tokens`` (*bool*)
          When True, request refresh tokens in addition to access tokens

          ``prefill_named_grant`` (*string*)
          Optionally prefill the named grant label on the consent page
    """

    def __init__(self, auth_client, requested_scopes=None,
                 redirect_uri=None, state='_default', verifier=None,
                 refresh_tokens=False, prefill_named_grant=None):
        self.auth_client = auth_client

        # set client_id, then check for validity
        self.client_id = auth_client.client_id
        if not self.client_id:
            logger.error('Invalid auth_client ID to start Native App Flow: {}'
                         .format(self.client_id))
            raise ValueError(
                'Invalid value for client_id. Got "{0}"'
                .format(self.client_id))

        # default to the default requested scopes
        self.requested_scopes = requested_scopes or DEFAULT_REQUESTED_SCOPES

        # default to `/v2/web/auth-code` on whatever environment we're looking
        # at -- most typically it will be `https://auth.globus.org/`
        self.redirect_uri = redirect_uri or (
            slash_join(auth_client.base_url, '/v2/web/auth-code'))

        # make a challenge and secret to keep
        # if the verifier is provided, it will just be passed back to us, and
        # if not, one will be generated
        self.verifier, self.challenge = make_native_app_challenge(verifier)

        # store the remaining parameters directly, with no transformation
        self.refresh_tokens = refresh_tokens
        self.state = state
        self.prefill_named_grant = prefill_named_grant

        logger.debug('Starting Native App Flow with params:')
        logger.debug('auth_client.client_id={}'.format(auth_client.client_id))
        logger.debug('redirect_uri={}'.format(self.redirect_uri))
        logger.debug('refresh_tokens={}'.format(refresh_tokens))
        logger.debug('state={}'.format(state))
        logger.debug('requested_scopes={}'.format(self.requested_scopes))
        logger.debug('verifier=<REDACTED>,challenge={}'.format(self.challenge))

        if prefill_named_grant is not None:
            logger.debug('prefill_named_grant={}'.format(
                self.prefill_named_grant))

    def get_authorize_url(self, additional_params=None):
        """
        Start a Native App flow by getting the authorization URL to which users
        should be sent.

        **Parameters**

            ``additional_params`` (*dict*)
              A ``dict`` or ``None``, which specifies additional query
              parameters to include in the authorize URL. Primarily for
              internal use

        :rtype: ``string``

        The returned URL string is encoded to be suitable to display to users
        in a link or to copy into their browser. Users will be redirected
        either to your provided ``redirect_uri`` or to the default location,
        with the ``auth_code`` embedded in a query parameter.
        """
        authorize_base_url = slash_join(self.auth_client.base_url,
                                        '/v2/oauth2/authorize')
        logger.debug('Building authorization URI. Base URL: {}'
                     .format(authorize_base_url))
        logger.debug('additional_params={}'.format(additional_params))

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.requested_scopes,
            'state': self.state,
            'response_type': 'code',
            'code_challenge': self.challenge,
            'code_challenge_method': 'S256',
            'access_type': (self.refresh_tokens and 'offline') or 'online'
        }
        if self.prefill_named_grant is not None:
            params['prefill_named_grant'] = self.prefill_named_grant
        if additional_params:
            params.update(additional_params)

        params = urlencode(params)
        return '{0}?{1}'.format(authorize_base_url, params)

    def exchange_code_for_tokens(self, auth_code):
        """
        The second step of the Native App flow, exchange an authorization code
        for access tokens (and refresh tokens if specified).

        :rtype: :class:`OAuthTokenResponse \
        <globus_sdk.auth.token_response.OAuthTokenResponse>`
        """
        logger.debug(('Performing Native App auth_code exchange. '
                      'Sending verifier and client_id'))
        return self.auth_client.oauth2_token(
            {'client_id': self.client_id,
             'grant_type': 'authorization_code',
             'code': auth_code.encode('utf-8'),
             'code_verifier': self.verifier,
             'redirect_uri': self.redirect_uri})
