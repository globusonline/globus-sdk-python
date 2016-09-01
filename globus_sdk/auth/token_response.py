import json
from globus_sdk.response import GlobusHTTPResponse


class GlobusOAuthTokenResponse(GlobusHTTPResponse):
    """
    Class for responses from the OAuth2 code for tokens exchange used in
    3-legged OAuth flows.
    """
    def __init__(self, *args, **kwargs):
        GlobusHTTPResponse.__init__(self, *args, **kwargs)
        self._by_resource_server = None

    @property
    def by_resource_server(self):
        """
        Representation of the token response in a ``dict`` indexed by resource
        server.

        Although ``GlobusOAuthTokenResponse.data`` is still available and
        valid, this representation is typically more desirable for applications
        doing their own inspection of access tokens and refresh tokens.
        """
        def _mk_item(source_dict):
            """
            Extract a set of fields into a new dict, allow for 'refresh_token'
            to be `None` when absent.
            """
            return {
                'scope': source_dict['scope'],
                'access_token': source_dict['access_token'],
                'refresh_token': source_dict.get('refresh_token'),
                'expires_in': source_dict['expires_in']
            }

        if self._by_resource_server is None:
            self._by_resource_server = {
                self['resource_server']: _mk_item(self)}
            self._by_resource_server.update(dict(
                (unprocessed_item['resource_server'],
                 _mk_item(unprocessed_item))
                for unprocessed_item in self['other_tokens']))

        return self._by_resource_server

    def __str__(self):
        # Make printing responses more convenient by only showing the
        # (typically important) token info
        return json.dumps(self.by_resource_server, indent=2)
