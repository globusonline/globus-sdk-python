import logging


from globus_sdk.version import __version__

from globus_sdk.response import GlobusResponse, GlobusHTTPResponse

from globus_sdk.exc import (
    GlobusError, GlobusSDKUsageError,
    GlobusAPIError, TransferAPIError, SearchAPIError,
    NetworkError, GlobusConnectionError, GlobusTimeoutError,
    GlobusConnectionTimeoutError)

from globus_sdk.authorizers import (
    NullAuthorizer, BasicAuthorizer, AccessTokenAuthorizer,
    RefreshTokenAuthorizer, ClientCredentialsAuthorizer)

from globus_sdk.auth import (
    AuthClient, NativeAppAuthClient, ConfidentialAppAuthClient)

from globus_sdk.transfer import TransferClient
from globus_sdk.transfer.data import TransferData, DeleteData

from globus_sdk.search import SearchClient, SearchQuery

from globus_sdk.local_endpoint import LocalGlobusConnectPersonal


__all__ = (
    "__version__",

    "GlobusResponse", "GlobusHTTPResponse",

    "GlobusError", "GlobusSDKUsageError",
    "GlobusAPIError", "TransferAPIError", "SearchAPIError",
    "NetworkError", "GlobusConnectionError", "GlobusTimeoutError",
    "GlobusConnectionTimeoutError",

    "NullAuthorizer", "BasicAuthorizer",
    "AccessTokenAuthorizer", "RefreshTokenAuthorizer",
    "ClientCredentialsAuthorizer",

    "AuthClient", "NativeAppAuthClient", "ConfidentialAppAuthClient",

    "TransferClient", "TransferData", "DeleteData",

    "SearchClient", "SearchQuery",

    'LocalGlobusConnectPersonal',
)


# configure logging for a library, per python best practices:
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
# NB: this won't work on py2.6 because `logging.NullHandler` wasn't added yet
try:
    nullhandler = logging.NullHandler()
except AttributeError:
    class MyNullHandler(logging.Handler):
        def emit(self, record):
            pass

        def handle(self, record):
            pass

        def createLock(self):
            self.lock = None

    nullhandler = MyNullHandler()
logging.getLogger('globus_sdk').addHandler(nullhandler)
