from __future__ import print_function

from globus_sdk.base import BaseClient, GlobusError


class NexusClient(BaseClient):
    def __init__(self, environment="default"):
        BaseClient.__init__(self, "nexus", environment)

    def get_goauth_token(self, username, password):
        """
        Legacy method for getting a GOAuth token from nexus using
        globusid username and password. Clients using this should
        be prepared to migrate to Globus Auth.

        Note that these tokens have a long lifetime and should be saved
        and re-used.
        """
        r = self.get('/goauth/token?grant_type=client_credentials',
                     auth=(username, password))
        try:
            return r.json_body['access_token']
        except KeyError:
            raise GlobusError(r)
        else:
            raise
