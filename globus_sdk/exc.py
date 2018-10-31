import logging

import requests
import six

logger = logging.getLogger(__name__)


class GlobusError(Exception):
    """
    Root of the Globus Exception hierarchy.
    Stub class.
    """


class GlobusSDKUsageError(GlobusError, ValueError):
    """
    A ``GlobusSDKUsageError`` may be thrown in cases in which the SDK
    detects that it is being used improperly.

    These errors typically indicate that some contract regarding SDK usage
    (e.g. required order of operations) has been violated.
    """


class GlobusAPIError(GlobusError):
    """
    Wraps errors returned by a REST API.

    :ivar http_status: HTTP status code (int)
    :ivar code: Error code from the API (str),
                or "Error" for unclassified errors
    :ivar message: Error message from the API. In general, this will be more
                   useful to developers, but there may be cases where it's
                   suitable for display to end users.
    """

    def __init__(self, r, *args, **kw):
        self._underlying_response = r
        self.http_status = r.status_code
        if "Content-Type" in r.headers and (
            "application/json" in r.headers["Content-Type"]
        ):
            logger.debug(
                (
                    "Content-Type on error is application/json. "
                    "Doing error load from JSON"
                )
            )
            try:
                self._load_from_json(r.json())
            except (KeyError, ValueError):
                logger.error(
                    (
                        "Error body could not be JSON decoded! "
                        "This means the Content-Type is wrong, or the "
                        "body is malformed!"
                    )
                )
                self._load_from_text(r.text)
        else:
            logger.debug(
                (
                    "Content-Type on error is unknown. "
                    "Failing over to error load as text (default)"
                )
            )
            # fallback to using the entire body as the message for all
            # other types
            self._load_from_text(r.text)
        args = self._get_args()
        GlobusError.__init__(self, *args)

    @property
    def raw_json(self):
        """
        Get the verbatim error message received from a Globus API, interpreted
        as a JSON string and evaluated as a *dict*

        If the body cannot be loaded as JSON, this is None
        """
        r = self._underlying_response
        if "Content-Type" in r.headers and (
            "application/json" in r.headers["Content-Type"]
        ):
            try:
                return r.json()
            except ValueError:
                logger.error(
                    (
                        "Error body could not be JSON decoded! "
                        "This means the Content-Type is wrong, or the "
                        "body is malformed!"
                    )
                )
                return None
        else:
            return None

    @property
    def raw_text(self):
        """
        Get the verbatim error message receved from a Globus API as a *string*
        """
        return self._underlying_response.text

    def _get_args(self):
        """
        Get arguments to pass to the Exception base class. These args are
        displayed in stack traces.
        """
        return (self.http_status, self.code, self.message)

    def _load_from_json(self, data):
        """
        Load error data from a JSON document. Must set at least
        code and message instance variables.
        """
        if "errors" in data:
            if len(data["errors"]) != 1:
                logger.warning(
                    (
                        "Doing JSON load of error response with multiple "
                        "errors. Exception data will only include the "
                        "first error, but there are really {} errors"
                    ).format(len(data["errors"]))
                )
            # TODO: handle responses with more than one error
            data = data["errors"][0]
        self.code = data["code"]
        if "message" in data:
            logger.debug(
                (
                    "Doing JSON load of error response with 'message' "
                    "field. There may also be a useful 'detail' field "
                    "to inspect"
                )
            )
            self.message = data["message"]
        else:
            self.message = data["detail"]

    def _load_from_text(self, text):
        """
        Load error data from a raw text body that is not JSON. Must set at
        least code and message instance variables.
        """
        self.code = "Error"
        self.message = text


class SearchAPIError(GlobusAPIError):
    """
    Error class for the Search API client. In addition to the
    inherited ``code`` and ``message`` instance variables, provides:

    :ivar error_data: Additional object returned in the error response. May be
                      a dict, list, or None.
    """

    def __init__(self, r):
        self.error_data = None
        GlobusAPIError.__init__(self, r)

    def _get_args(self):
        return (self.http_status, self.code, self.message)

    def _load_from_json(self, data):
        self.code = data["code"]
        self.message = data["message"]
        self.error_data = data.get("error_data")


class TransferAPIError(GlobusAPIError):
    """
    Error class for the Transfer API client. In addition to the
    inherited ``code`` and ``message`` instance variables, provides:

    :ivar request_id: Unique identifier for the request, which should be
                      provided when contacting support@globus.org.
    """

    def __init__(self, r):
        self.request_id = None
        GlobusAPIError.__init__(self, r)

    def _get_args(self):
        return (self.http_status, self.code, self.message, self.request_id)

    def _load_from_json(self, data):
        self.code = data["code"]
        self.message = data["message"]
        self.request_id = data["request_id"]


class AuthAPIError(GlobusAPIError):
    """
    Error class for the API components of Globus Auth.

    Customizes JSON parsing.
    """

    def _load_from_json(self, data):
        """
        Load error data from a JSON document.

        Looks for a top-level "error" attribute in addition to the other
        standard API error attributes. It's not clear whether or not this
        should be a behavior of the base class.

        Handles the case in which an error does not conform to base-class
        expectations with a `no_extractable_message` message.
        """
        if "errors" in data:
            if len(data["errors"]) != 1:
                logger.warning(
                    (
                        "Doing JSON load of error response with multiple "
                        "errors. Exception data will only include the "
                        "first error, but there are really {} errors"
                    ).format(len(data["errors"]))
                )
            # TODO: handle responses with more than one error
            data = data["errors"][0]

        self.code = data.get("code", "Error")

        if "message" in data:
            self.message = data["message"]
        elif "detail" in data:
            self.message = data["detail"]
        elif "error" in data and isinstance(data["error"], six.string_types):
            self.message = data["error"]
        else:
            self.message = "no_extractable_message"


class InvalidDocumentBodyError(GlobusError):
    """
    The body of the document being sent to Globus is somehow malformed.

    For example, a call that requires a specific format (XML, JSON, etc.) not
    being given data in that format.
    """


# Wrappers around requests exceptions, so the SDK is API independent.
class NetworkError(GlobusError):
    """
    Error communicating with the REST API server.

    Holds onto original exception data, but also takes a message
    to explain potentially confusing or inconsistent exceptions passed to us
    """

    def __init__(self, msg, exc, *args, **kw):
        super(NetworkError, self).__init__(msg)
        self.underlying_exception = exc


class GlobusTimeoutError(NetworkError):
    """The REST request timed out."""


class GlobusConnectionTimeoutError(GlobusTimeoutError):
    """The request timed out during connection establishment.
    These errors are safe to retry."""


class GlobusConnectionError(NetworkError):
    """A connection error occured while making a REST request."""


class ConfigError(GlobusError):
    """An error reading or writing from the configuration file."""


class RequestedScopesMismatch(ConfigError):
    """Requested scopes differ from scopes saved to config."""


class LoadedTokensExpired(ConfigError):
    """Tokens loaded from disk have expired since last login."""


class LocalServerError(GlobusError):
    """Error encountered with local server used for native auth."""


def convert_request_exception(exc):
    """Converts incoming requests.Exception to a Globus NetworkError"""

    if isinstance(exc, requests.ConnectTimeout):
        return GlobusConnectionTimeoutError("ConnectTimeoutError on request", exc)
    if isinstance(exc, requests.Timeout):
        return GlobusTimeoutError("TimeoutError on request", exc)
    elif isinstance(exc, requests.ConnectionError):
        return GlobusConnectionError("ConnectionError on request", exc)
    else:
        return NetworkError("NetworkError on request", exc)
