import logging

from globus_sdk.authorizers.base import GlobusAuthorizer

logger = logging.getLogger(__name__)


class AccessTokenAuthorizer(GlobusAuthorizer):
    """
    Implements Authorization using a single Access Token with no Refresh
    Tokens. This is sent as a Bearer token in the header -- basically
    unadorned.

    **Parameters**

        ``access_token`` (*string*)
          An access token for Globus Auth
    """
    def __init__(self, access_token):
        logger.info(("Setting up an AccessTokenAuthorizer. It will use an "
                     "auth type of Bearer and cannot handle 401s."))
        logger.debug('Bearer token ends in "...{0}" (last 5 chars)'
                     .format(access_token[-5:]))
        self.access_token = access_token
        self.header_val = "Bearer %s" % access_token

    def set_authorization_header(self, header_dict):
        """
        Sets the ``Authorization`` header to
        "Bearer <access_token>"
        """
        logger.debug(("Setting AccessToken Authorization Header: "
                      '"Bearer ...{0}" (last 5 chars)')
                     .format(self.header_val[-5:]))
        header_dict['Authorization'] = self.header_val
