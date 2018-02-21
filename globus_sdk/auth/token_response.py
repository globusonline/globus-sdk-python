import logging
import json
import requests
import time
import six

import jwt

from globus_sdk.response import GlobusHTTPResponse

logger = logging.getLogger(__name__)


def _convert_token_info_dict(source_dict):
    """
    Extract a set of fields into a new dict for indexing by resource server.
    Allow for these fields to be `None` when absent:
        - "refresh_token"
        - "token_type"
    """
    expires_in = source_dict.get('expires_in', 0)

    return {
        'scope': source_dict['scope'],
        'access_token': source_dict['access_token'],
        'refresh_token': source_dict.get('refresh_token'),
        'token_type': source_dict.get('token_type'),
        'expires_at_seconds': int(time.time() + expires_in),
        'resource_server': source_dict['resource_server']
    }


class _ByScopesGetter(object):
    """
    A fancy dict-like object for looking up token data by scope name.
    Allows usage like

    >>> tokens = OAuthTokenResponse(...)
    >>> tok = tokens.by_scopes['openid profile']['access_token']
    """
    def __init__(self, scope_map):
        self.scope_map = scope_map

    def __str__(self):
        return json.dumps(self.scope_map)

    def __iter__(self):
        """iteration gets you every individual scope"""
        return iter(self.scope_map.keys())

    def __getitem__(self, scopename):
        if not isinstance(scopename, six.string_types):
            raise KeyError('by_scopes cannot contain non-string value "{0}"'
                           .format(scopename))

        # split on spaces
        scopes = scopename.split()
        # collect every matching token in a set to dedup
        # but collect actual results (dicts) in a list
        rs_names = set()
        toks = []
        for scope in scopes:
            try:
                rs_names.add(self.scope_map[scope]['resource_server'])
                toks.append(self.scope_map[scope])
            except KeyError:
                raise KeyError(('Scope specifier "{0}" contains scope "{1}" '
                                "which was not found"
                                ).format(scopename, scope))
        # if there isn't exactly 1 token, it's an error
        if len(rs_names) != 1:
            raise KeyError(
                'Scope specifier "{0}" did not match exactly one token!'
                .format(scopename))
        # pop the only element in the set
        return toks.pop()

    def __contains__(self, item):
        """
        contains is driven by checking against getitem
        that way, the definitions are always "in sync" if we update them in
        the future
        """
        try:
            self.__getitem__(item)
            return True
        except KeyError:
            pass

        return False


class OAuthTokenResponse(GlobusHTTPResponse):
    """
    Class for responses from the OAuth2 code for tokens exchange used in
    3-legged OAuth flows.
    """
    def __init__(self, *args, **kwargs):
        GlobusHTTPResponse.__init__(self, *args, **kwargs)
        self._init_rs_dict()
        self._init_scopes_getter()

    def _init_scopes_getter(self):
        scope_map = {}
        for rs, tok_data in self._by_resource_server.items():
            for s in tok_data["scope"].split():
                scope_map[s] = tok_data
        self._by_scopes = _ByScopesGetter(scope_map)

    def _init_rs_dict(self):
        # call the helper at the top level
        self._by_resource_server = {
            self['resource_server']: _convert_token_info_dict(self)
        }
        # call the helper on everything in 'other_tokens'
        self._by_resource_server.update(dict(
            (unprocessed_item['resource_server'],
             _convert_token_info_dict(unprocessed_item))
            for unprocessed_item in self['other_tokens']))

    @property
    def by_resource_server(self):
        """
        Representation of the token response in a ``dict`` indexed by resource
        server.

        Although ``OAuthTokenResponse.data`` is still available and
        valid, this representation is typically more desirable for applications
        doing inspection of access tokens and refresh tokens.
        """
        return self._by_resource_server

    @property
    def by_scopes(self):
        """
        Representation of the token response in a dict-like object indexed by
        scope name (or even space delimited scope names, so long as they match
        the same token).

        If you request scopes `scope1 scope2 scope3`, where `scope1` and
        `scope2` are for the same service (and therefore map to the same
        token), but `scope3` is for a different service, the following forms of
        access are valid:

        >>> tokens = ...
        >>> # single scope
        >>> token_data = tokens.by_scopes['scope1']
        >>> token_data = tokens.by_scopes['scope2']
        >>> token_data = tokens.by_scopes['scope3']
        >>> # matching scopes
        >>> token_data = tokens.by_scopes['scope1 scope2']
        >>> token_data = tokens.by_scopes['scope2 scope1']
        """
        return self._by_scopes

    def decode_id_token(self, auth_client=None):
        """
        A parsed ID Token (OIDC) as a dict.

        **Parameters**

            ``auth_client`` (:class:`AuthClient <globus_sdk.AuthClient>`)
              Deprecated parameter for providing the AuthClient used to request
              this token back to the OAuthTokenResponse. The SDK now tracks
              this internally, so it is no longer necessary.
        """
        logger.info('Decoding ID Token "{0}"'.format(self['id_token']))

        # warn (not error) on older usage pattern, but still respect it
        # FIXME: should be deprecated and removed in SDK v2
        if auth_client:
            logger.warn(
                'Providing an auth_client to decode_id_token is no '
                'longer required and may be deprecated in a future version '
                'of the Globus SDK')
        else:
            auth_client = self._client

        logger.debug('Fetch JWK Data: Start')
        oidc_conf = auth_client.get('/.well-known/openid-configuration')
        jwks_uri = oidc_conf['jwks_uri']
        signing_algos = oidc_conf['id_token_signing_alg_values_supported']

        # use the auth_client's decision on ssl_verify=yes/no
        jwk_data = requests.get(jwks_uri, verify=auth_client._verify).json()
        logger.debug('Fetch JWK Data: Complete')
        # decode from JWK to an RSA PEM key for JWT decoding
        jwk_as_pem = jwt.algorithms.RSAAlgorithm.from_jwk(
            json.dumps(jwk_data['keys'][0]))

        return jwt.decode(
            self['id_token'], jwk_as_pem,
            algorithms=signing_algos, audience=auth_client.client_id)

    def __str__(self):
        # Make printing responses more convenient by only showing the
        # (typically important) token info
        return json.dumps(self.by_resource_server, indent=2)


class OAuthDependentTokenResponse(OAuthTokenResponse):
    """
    Class for responses from the OAuth2 code for tokens retrieved by the
    OAuth2 Dependent Token Extension Grant. For more complete docs, see
    :meth:`oauth2_get_dependent_tokens \
    <globus_sdk.ConfidentialAppAuthClient.oauth2_get_dependent_tokens>`
    """
    def _init_rs_dict(self):
        # call the helper on everything in the response array
        self._by_resource_server = dict(
            (unprocessed_item['resource_server'],
             _convert_token_info_dict(unprocessed_item))
            for unprocessed_item in self.data)

    def decode_id_token(self, auth_client):
        # just in case
        raise NotImplementedError(
            ('OAuthDependentTokenResponse.decode_id_token() is not and cannot '
             'be implemented. Dependent Tokens data does not include an '
             'id_token'))
