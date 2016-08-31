import json
from globus_sdk.response import GlobusHTTPResponse


class GlobusOAuthTokenResponse(GlobusHTTPResponse):
    """
    Class for responses from the OAuth2 code for tokens exchange used in
    3-legged OAuth flows.
    """
    @property
    def tokens(self):
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

        ret = {self['resource_server']: _mk_item(self)}
        ret.update(dict(
            (unprocessed_item['resource_server'], _mk_item(unprocessed_item))
            for unprocessed_item in self['other_tokens']))

        return ret

    def __str__(self):
        # Make printing responses more convenient by only showing the
        # (typically important) token info
        return json.dumps(self.tokens, indent=2)
