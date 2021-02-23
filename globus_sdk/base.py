import json
import logging
import typing
import urllib.parse

import requests

from globus_sdk import config, exc
from globus_sdk.response import GlobusHTTPResponse
from globus_sdk.version import __version__


class ClientLogAdapter(logging.LoggerAdapter):
    """
    Stuff in the memory location of the client to make log records unambiguous.
    """

    def process(self, msg, kwargs):
        return "[instance:{}] {}".format(id(self.extra["client"]), msg), kwargs

    def warn(self, *args, **kwargs):
        """
        NOTE: although Logger.warn() is deprecated in python, we've now made
        it part of the interface for clients. We should only remove this
        carefully, as someone may be leveraging something like

        >>> TransferClient.logger.warn(...)

        even though that would be a bad idea. At the very least, removing it
        should be a considered move, not just thrown in with warn() ->
        warning() cleanup.
        """
        return self.warning(*args, **kwargs)


class BaseClient:
    r"""
    Simple client with error handling for Globus REST APIs. Implemented
    as a wrapper around a ``requests.Session`` object, with a simplified
    interface that does not directly expose anything from requests.

    You should *never* try to directly instantiate a ``BaseClient``.

    :param authorizer: A ``GlobusAuthorizer`` which will generate Authorization headers
    :type authorizer: :class:`GlobusAuthorizer\
        <globus_sdk.authorizers.base.GlobusAuthorizer>`
    :param app_name: Optional "nice name" for the application. Has no bearing on the
        semantics of client actions. It is just passed as part of the User-Agent
        string, and may be useful when debugging issues with the Globus Team
    :type app_name: str
    :param http_timeout: Number of seconds to wait on HTTP connections. Default is 60.
        A value of -1 indicates that no timeout should be used (requests can hang
        indefinitely).
    :type http_timeout: float

    All other parameters are for internal use and should be ignored.
    """

    # Can be overridden by subclasses, but must be a subclass of GlobusError
    error_class: typing.Type[exc.GlobusAPIError] = exc.GlobusAPIError
    default_response_class: typing.Type[GlobusHTTPResponse] = GlobusHTTPResponse
    # a collection of authorizer types, or None to indicate "any"
    allowed_authorizer_types: typing.Optional[typing.List[typing.Type]] = None

    BASE_USER_AGENT = f"globus-sdk-py-{__version__}"

    def __init__(
        self,
        service,
        environment=None,
        base_url=None,
        base_path=None,
        authorizer=None,
        app_name=None,
        http_timeout=None,
        *args,
        **kwargs,
    ):
        self._init_logger_adapter()
        self.logger.info(
            'Creating client of type {} for service "{}"'.format(type(self), service)
        )
        # if restrictions have been placed by a child class on the allowed
        # authorizer types, make sure we are not in violation of those
        # constraints
        if self.allowed_authorizer_types is not None and (
            authorizer is not None
            and type(authorizer) not in self.allowed_authorizer_types
        ):
            self.logger.error(
                "{} doesn't support authorizer={}".format(type(self), type(authorizer))
            )
            raise exc.GlobusSDKUsageError(
                (
                    "{} can only take authorizers from {}, but you have provided {}"
                ).format(type(self), self.allowed_authorizer_types, type(authorizer))
            )

        # if an environment was passed, it will be used, but otherwise lookup
        # the env var -- and in the special case of `production` translate to
        # `default`, regardless of the source of that value
        # logs the environment when it isn't `default`
        self.environment = config.get_globus_environ(inputenv=environment)

        self.authorizer = authorizer

        if base_url is None:
            self.base_url = config.get_service_url(self.environment, service)
        else:
            self.base_url = base_url
        self.base_url = slash_join(self.base_url, base_path)

        # setup the basics for wrapping a Requests Session
        # including basics for internal header dict
        self._session = requests.Session()
        self._headers = {
            "Accept": "application/json",
            "User-Agent": self.BASE_USER_AGENT,
        }

        # verify SSL? Usually true
        self._verify = config.get_ssl_verify(self.environment)
        # HTTP connection timeout
        # this is passed verbatim to `requests`, and we therefore technically
        # support a tuple for connect/read timeouts, but we don't need to
        # advertise that... Just declare it as an float value
        if http_timeout is None:
            http_timeout = config.get_http_timeout(self.environment)
        self._http_timeout = http_timeout
        # handle -1 by passing None to requests
        if self._http_timeout == -1:
            self._http_timeout = None

        # set application name if given
        self.app_name = None
        if app_name is not None:
            self.set_app_name(app_name)

    def _init_logger_adapter(self):
        """
        Create & assign the self.logger LoggerAdapter
        Used when initializing a new client, or unpickling.

        Technically, this could result in a state change across a
        pickle/unpickle -- file handles and other handlers could be detached,
        etc.
        However, that's better than a hard-fail on pickle.dump(s) calls.

        Also, so long as loggers are attached at the module level -- as they
        really ought to be -- everything will be fine.
        """
        # get the fully qualified name of the client class, so that it's a
        # child of globus_sdk
        self.logger = ClientLogAdapter(
            logging.getLogger(self.__module__ + "." + self.__class__.__name__),
            {"client": self},
        )

    def __getstate__(self):
        """
        Render to a serializable dict for pickle.dump(s)
        """
        self.logger.info("__getstate__() called; client being pickled")
        d = dict(self.__dict__)  # copy
        del d["logger"]
        return d

    def __setstate__(self, d):
        """
        Load from a serialized format, as in pickle.load(s)
        """
        self._init_logger_adapter()
        self.__dict__.update(d)
        self.logger.info("__setstate__() finished; client unpickled")

    def set_app_name(self, app_name):
        """
        Set an application name to send to Globus services as part of the User
        Agent.

        Application developers are encouraged to set an app name as a courtesy
        to the Globus Team, and to potentially speed resolution of issues when
        interacting with Globus Support.
        """
        self.app_name = app_name
        self._headers["User-Agent"] = f"{self.BASE_USER_AGENT}/{app_name}"

    def qjoin_path(self, *parts):
        return "/" + "/".join(urllib.parse.quote(part) for part in parts)

    def get(self, path, params=None, headers=None, response_class=None, retry_401=True):
        """
        Make a GET request to the specified path.

        :param path: Path for the request, with or without leading slash
        :type path: str
        :param params: Parameters to be encoded as a query string
        :type params: dict
        :param headers: HTTP headers to add to the request
        :type headers: dict
        :param response_class: Class for response object, overrides the client's
            ``default_response_class``
        :type response_class: class
        :param retry_401: Retry on 401 responses with fresh Authorization if
            ``self.authorizer`` supports it
        :type retry_401: bool

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        self.logger.debug(f"GET to {path} with params {params}")
        return self._request(
            "GET",
            path,
            params=params,
            headers=headers,
            response_class=response_class,
            retry_401=retry_401,
        )

    def post(
        self,
        path,
        json_body=None,
        params=None,
        headers=None,
        text_body=None,
        response_class=None,
        retry_401=True,
    ):
        """
        Make a POST request to the specified path.

        :param path: Path for the request, with or without leading slash
        :type path: str
        :param params: Parameters to be encoded as a query string
        :type params: dict
        :param headers: HTTP headers to add to the request
        :type headers: dict
        :param json_body: Data which will be JSON encoded as the body of the request
        :type json_body: dict
        :param text_body: Either a raw string that will serve as the request body, or a
            dict which will be HTTP Form encoded
        :type text_body: str or dict
        :param response_class: Class for response object, overrides the client's
            ``default_response_class``
        :type response_class: class
        :param retry_401: Retry on 401 responses with fresh Authorization if
            ``self.authorizer`` supports it
        :type retry_401: bool

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        self.logger.debug(f"POST to {path} with params {params}")
        return self._request(
            "POST",
            path,
            json_body=json_body,
            params=params,
            headers=headers,
            text_body=text_body,
            response_class=response_class,
            retry_401=retry_401,
        )

    def delete(
        self, path, params=None, headers=None, response_class=None, retry_401=True
    ):
        """
        Make a DELETE request to the specified path.

        :param path: Path for the request, with or without leading slash
        :type path: str
        :param params: Parameters to be encoded as a query string
        :type params: dict
        :param headers: HTTP headers to add to the request
        :type headers: dict
        :param response_class: Class for response object, overrides the client's
            ``default_response_class``
        :type response_class: class
        :param retry_401: Retry on 401 responses with fresh Authorization if
            ``self.authorizer`` supports it
        :type retry_401: bool

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        self.logger.debug(f"DELETE to {path} with params {params}")
        return self._request(
            "DELETE",
            path,
            params=params,
            headers=headers,
            response_class=response_class,
            retry_401=retry_401,
        )

    def put(
        self,
        path,
        json_body=None,
        params=None,
        headers=None,
        text_body=None,
        response_class=None,
        retry_401=True,
    ):
        """
        Make a PUT request to the specified path.

        :param path: Path for the request, with or without leading slash
        :type path: str
        :param params: Parameters to be encoded as a query string
        :type params: dict
        :param headers: HTTP headers to add to the request
        :type headers: dict
        :param json_body: Data which will be JSON encoded as the body of the request
        :type json_body: dict
        :param text_body: Either a raw string that will serve as the request body, or a
            dict which will be HTTP Form encoded
        :type text_body: str or dict
        :param response_class: Class for response object, overrides the client's
            ``default_response_class``
        :type response_class: class
        :param retry_401: Retry on 401 responses with fresh Authorization if
            ``self.authorizer`` supports it
        :type retry_401: bool

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        self.logger.debug(f"PUT to {path} with params {params}")
        return self._request(
            "PUT",
            path,
            json_body=json_body,
            params=params,
            headers=headers,
            text_body=text_body,
            response_class=response_class,
            retry_401=retry_401,
        )

    def patch(
        self,
        path,
        json_body=None,
        params=None,
        headers=None,
        text_body=None,
        response_class=None,
        retry_401=True,
    ):
        """
        Make a PATCH request to the specified path.

        :param path: Path for the request, with or without leading slash
        :type path: str
        :param params: Parameters to be encoded as a query string
        :type params: dict
        :param headers: HTTP headers to add to the request
        :type headers: dict
        :param json_body: Data which will be JSON encoded as the body of the request
        :type json_body: dict
        :param text_body: Either a raw string that will serve as the request body, or a
            dict which will be HTTP Form encoded
        :type text_body: str or dict
        :param response_class: Class for response object, overrides the client's
            ``default_response_class``
        :type response_class: class
        :param retry_401: Retry on 401 responses with fresh Authorization if
            ``self.authorizer`` supports it
        :type retry_401: bool

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        self.logger.debug(f"PATCH to {path} with params {params}")
        return self._request(
            "PATCH",
            path,
            json_body=json_body,
            params=params,
            headers=headers,
            text_body=text_body,
            response_class=response_class,
            retry_401=retry_401,
        )

    def _request(
        self,
        method,
        path,
        params=None,
        headers=None,
        json_body=None,
        text_body=None,
        response_class=None,
        retry_401=True,
    ):
        """
        Send an HTTP request

        :param method: HTTP request method, as an all caps string
        :type method: str
        :param path: Path for the request, with or without leading slash
        :type path: str
        :param params: Parameters to be encoded as a query string
        :type params: dict
        :param headers: HTTP headers to add to the request
        :type headers: dict
        :param json_body: Data which will be JSON encoded as the body of the request
        :type json_body: dict
        :param text_body: Either a raw string that will serve as the request body, or a
            dict which will be HTTP Form encoded
        :type text_body: str or dict
        :param response_class: Class for response object, overrides the client's
            ``default_response_class``
        :type response_class: class
        :param retry_401: Retry on 401 responses with fresh Authorization if
            ``self.authorizer`` supports it
        :type retry_401: bool

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        # copy
        rheaders = dict(self._headers)
        # expand
        if headers is not None:
            rheaders.update(headers)

        if json_body is not None:
            assert text_body is None
            text_body = json.dumps(json_body)
            # set appropriate content-type header
            rheaders.update({"Content-Type": "application/json"})

        # add Authorization header, or (if it's a NullAuthorizer) possibly
        # explicitly remove the Authorization header
        if self.authorizer is not None:
            self.logger.debug(
                "request will have authorization of type {}".format(
                    type(self.authorizer)
                )
            )
            self.authorizer.set_authorization_header(rheaders)

        # if a client is asked to make a request against a full URL, not just the path
        # component, then do not resolve the path, simply pass it through as the URL
        if path.startswith("https://") or path.startswith("http://"):
            url = path
        else:
            url = slash_join(self.base_url, path)
        self.logger.debug(f"request will hit URL:{url}")

        # because a 401 can trigger retry, we need to wrap the retry-able thing
        # in a method
        def send_request():
            try:
                return self._session.request(
                    method=method,
                    url=url,
                    headers=rheaders,
                    params=params,
                    data=text_body,
                    verify=self._verify,
                    timeout=self._http_timeout,
                )
            except requests.RequestException as e:
                self.logger.error("NetworkError on request")
                raise exc.convert_request_exception(e)

        # initial request
        r = send_request()

        self.logger.debug(f"Request made to URL: {r.url}")

        # potential 401 retry handling
        if r.status_code == 401 and retry_401 and self.authorizer is not None:
            self.logger.debug("request got 401, checking retry-capability")
            # note that although handle_missing_authorization returns a T/F
            # value, it may actually mutate the state of the authorizer and
            # therefore change the value set by the `set_authorization_header`
            # method
            if self.authorizer.handle_missing_authorization():
                self.logger.debug("request can be retried")
                self.authorizer.set_authorization_header(rheaders)
                r = send_request()

        if 200 <= r.status_code < 400:
            self.logger.debug(f"request completed with response code: {r.status_code}")
            if response_class is None:
                return self.default_response_class(r, client=self)
            else:
                return response_class(r, client=self)

        self.logger.debug(
            f"request completed with (error) response code: {r.status_code}"
        )
        raise self.error_class(r)


def slash_join(a, b):
    """
    Join a and b with a single slash, regardless of whether they already
    contain a trailing/leading slash or neither.
    """
    if not b:  # "" or None, don't append a slash
        return a
    if a.endswith("/"):
        if b.startswith("/"):
            return a[:-1] + b
        return a + b
    if b.startswith("/"):
        return a + b
    return a + "/" + b


def merge_params(base_params, **more_params):
    """
    Merge additional keyword arguments into a base dictionary of keyword
    arguments. Only inserts additional kwargs which are not None.
    This way, we can accept a bunch of named kwargs, a collector of additional
    kwargs, and then put them together sensibly as arguments to another
    function (typically BaseClient.get() or a variant thereof).

    For example:

    >>> def ep_search(self, filter_scope=None, filter_fulltext=None, **params):
    >>>     # Yes, this is a side-effecting function, it doesn't return a new
    >>>     # dict because it's way simpler to update in place
    >>>     merge_params(
    >>>         params, filter_scope=filter_scope,
    >>>         filter_fulltext=filter_fulltext)
    >>>     return self.get('endpoint_search', params=params)

    this is a whole lot cleaner than the alternative form:

    >>> def ep_search(self, filter_scope=None, filter_fulltext=None, **params):
    >>>     if filter_scope is not None:
    >>>         params['filter_scope'] = filter_scope
    >>>     if filter_fulltext is not None:
    >>>         params['filter_scope'] = filter_scope
    >>>     return self.get('endpoint_search', params=params)

    the second form exposes a couple of dangers that are obviated in the first
    regarding correctness, like the possibility of doing

    >>>     if filter_scope:
    >>>         params['filter_scope'] = filter_scope

    which is wrong (!) because filter_scope='' is a theoretically valid,
    real argument we want to pass.
    The first form will also prove shorter and easier to write for the most
    part.
    """
    for param in more_params:
        if more_params[param] is not None:
            base_params[param] = more_params[param]


def safe_stringify(value):
    """
    Converts incoming value to a unicode string. Convert bytes by decoding,
    anything else has __str__ called.
    Strings are checked to avoid duplications
    """
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)
