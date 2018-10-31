import logging

from globus_sdk.auth import (
    AuthClient,
    ConfidentialAppAuthClient,
    NativeAppAuthClient,
    native_auth,
)
from globus_sdk.authorizers import (
    AccessTokenAuthorizer,
    BasicAuthorizer,
    ClientCredentialsAuthorizer,
    NullAuthorizer,
    RefreshTokenAuthorizer,
)
from globus_sdk.exc import (
    AuthAPIError,
    GlobusAPIError,
    GlobusConnectionError,
    GlobusConnectionTimeoutError,
    GlobusError,
    GlobusSDKUsageError,
    GlobusTimeoutError,
    NetworkError,
    SearchAPIError,
    TransferAPIError,
)
from globus_sdk.local_endpoint import LocalGlobusConnectPersonal
from globus_sdk.response import GlobusHTTPResponse, GlobusResponse
from globus_sdk.search import SearchClient, SearchQuery
from globus_sdk.transfer import TransferClient
from globus_sdk.transfer.data import DeleteData, TransferData
from globus_sdk.version import __version__

__all__ = (
    "__version__",
    "GlobusResponse",
    "GlobusHTTPResponse",
    "GlobusError",
    "GlobusSDKUsageError",
    "GlobusAPIError",
    "AuthAPIError",
    "TransferAPIError",
    "SearchAPIError",
    "NetworkError",
    "GlobusConnectionError",
    "GlobusTimeoutError",
    "GlobusConnectionTimeoutError",
    "NullAuthorizer",
    "BasicAuthorizer",
    "AccessTokenAuthorizer",
    "RefreshTokenAuthorizer",
    "ClientCredentialsAuthorizer",
    "AuthClient",
    "NativeAppAuthClient",
    "native_auth",
    "ConfidentialAppAuthClient",
    "TransferClient",
    "TransferData",
    "DeleteData",
    "SearchClient",
    "SearchQuery",
    "LocalGlobusConnectPersonal",
)


# configure logging for a library, per python best practices:
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
# NB: this won't work on py2.6 because `logging.NullHandler` wasn't added yet
logging.getLogger("globus_sdk").addHandler(logging.NullHandler())
