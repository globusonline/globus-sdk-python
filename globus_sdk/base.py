import json
import base64

import requests

from six.moves.urllib.parse import quote

from globus_sdk import config, exc
from globus_sdk.version import __version__
from globus_sdk.response import GlobusHTTPResponse


class BaseClient(object):
    """
    Simple client with error handling for Globus REST APIs. Implemented
    as a wrapper around a ``requests.Session`` object, with a simplified
    interface that does not directly expose anything from requests.

    :param token: optional bearer token, scoped for the service matching the
                  client's class
    :param app_name: optional "nice name" for the application

    If ``token`` is omitted, the client will attempt to load a token from the
    SDK config file instead.

    ``app_name`` has no bearing on the semantics of client actions. It is just
    passed as part of the User-Agent string, and may be useful when debugging
    issues with the Globus Team.

    All other arguments are for internal use and should be ignored.


    You should *never* try to directly instantiate a ``BaseClient``.
    """

    # Can be overridden by subclasses, but must be a subclass of GlobusError
    error_class = exc.GlobusAPIError
    default_response_class = GlobusHTTPResponse

    AUTHTYPE_TOKEN = "token"
    AUTHTYPE_BASIC = "basic"

    BASE_USER_AGENT = 'globus-sdk-py-{0}'.format(__version__)

    def __init__(self, service, environment=config.get_default_environ(),
                 base_path=None, token=None, app_name=None):
        self.environment = environment

        self.base_url = config.get_service_url(environment, service)
        if base_path is not None:
            self.base_url = slash_join(self.base_url, base_path)

        # setup the basics for wrapping a Requests Session
        # including basics for internal header dict
        self._session = requests.Session()
        self._headers = {
            'Accept': 'application/json',
            'User-Agent': self.BASE_USER_AGENT
        }

        # load a token for the client's service if it is not given as a param
        # assign the result
        if not token:
            token = self.config_load_token()
        self.set_token(token)

        # verify SSL? Usually true
        self._verify = config.get_ssl_verify(environment)

        # set application name if given
        self.app_name = None
        if app_name is not None:
            self.set_app_name(app_name)

    def set_token(self, token):
        """
        Set bearer token authentication for this client.
        Overrides any token or basic auth header that may have been set by a
        prior invocation or by
        :func:`set_auth_basic <globus_sdk.base.BaseClient.set_auth_basic>`
        """
        self.auth_type = self.AUTHTYPE_TOKEN
        self._headers["Authorization"] = "Bearer %s" % token

    def set_auth_basic(self, username, password):
        """
        Set basic authentication for this client to the base64 encoding of
        ``<username>:<password>``.
        Overrides any auth token or basic auth header that may have been set by
        a prior invocation or by
        :func:`set_token <globus_sdk.base.BaseClient.set_token>`
        """
        self.auth_type = self.AUTHTYPE_BASIC
        encoded = base64.b64encode("%s:%s" % (username, password))
        self._headers["Authorization"] = "Basic %s" % encoded

    def set_app_name(self, app_name):
        """
        Set an application name to send to Globus services as part of the User
        Agent.

        Application developers are encouraged to set an app name as a courtesy
        to the Globus Team, and to potentially speed resolution of issues when
        interacting with Globus Support.
        """
        self.app_name = app_name
        self._headers['User-Agent'] = '{0}/{1}'.format(self.BASE_USER_AGENT,
                                                       app_name)

    def config_load_token(self):
        raise NotImplementedError(
            ('The BaseClient does not have a service token type associated '
             'with it. config_load_token() must be defined by a subclass '
             'because tokens are associated with services.'))

    def qjoin_path(self, *parts):
        return "/" + "/".join(quote(part) for part in parts)

    def get(self, path, params=None, headers=None, no_auth_header=False,
            response_class=None):
        """
        Make a GET request to the specified path.

        :param path: path for the request, with or without leading slash
        :param params: dict to be encoded as a query string
        :param headers: dict of HTTP headers to add to the request
        :param no_auth_header: When True, suppress the Authorization header
        :param response_class: class for response object, overrides the
                               client's ``default_response_class``

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        return self._request("GET", path, params=params, headers=headers,
                             no_auth_header=no_auth_header,
                             response_class=response_class)

    def post(self, path, json_body=None, params=None, headers=None,
             text_body=None, no_auth_header=False, response_class=None):
        """
        Make a POST request to the specified path.

        :param path: path for the request, with or without leading slash
        :param params: dict to be encoded as a query string
        :param headers: dict of HTTP headers to add to the request
        :param no_auth_header: When True, suppress the Authorization header
        :param json_body: dict that will be encoded as a JSON request body
        :param text_body: raw string that will be the request body
        :param response_class: class for response object, overrides the
                               client's ``default_response_class``

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        return self._request("POST", path, json_body=json_body, params=params,
                             headers=headers, text_body=text_body,
                             response_class=response_class,
                             no_auth_header=no_auth_header)

    def delete(self, path, params=None, headers=None, no_auth_header=False,
               response_class=None):
        """
        Make a DELETE request to the specified path.

        :param path: path for the request, with or without leading slash
        :param params: dict to be encoded as a query string
        :param headers: dict of HTTP headers to add to the request
        :param no_auth_header: When True, suppress the Authorization header
        :param response_class: class for response object, overrides the
                               client's ``default_response_class``

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        return self._request("DELETE", path, params=params,
                             headers=headers, no_auth_header=no_auth_header,
                             response_class=response_class)

    def put(self, path, json_body=None, params=None, headers=None,
            text_body=None, no_auth_header=False, response_class=None):
        """
        Make a PUT request to the specified path.

        :param path: path for the request, with or without leading slash
        :param params: dict to be encoded as a query string
        :param headers: dict of HTTP headers to add to the request
        :param no_auth_header: When True, suppress the Authorization header
        :param json_body: dict that will be encoded as a JSON request body
        :param text_body: raw string that will be the request body
        :param response_class: class for response object, overrides the
                               client's ``default_response_class``

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        return self._request("PUT", path, json_body=json_body, params=params,
                             headers=headers, text_body=text_body,
                             no_auth_header=no_auth_header,
                             response_class=response_class)

    def _request(self, method, path, params=None, headers=None,
                 json_body=None, text_body=None, no_auth_header=False,
                 response_class=None):
        """
        :param method: HTTP request method, as an all caps string
        :param path: path for the request, with or without leading slash
        :param headers: dict containing additional headers for the request
        :param params: dict to be encoded as a query string
        :param no_auth_header: When True, suppress the Authorization header
        :param json_body: dict that will be encoded as a JSON request body
        :param text_body: raw string that will be the request body
        :param response_class: class for response object, overrides the
                               client's ``default_response_class``

        :return: :class:`GlobusHTTPResponse \
        <globus_sdk.response.GlobusHTTPResponse>` object
        """
        if json_body is not None:
            assert text_body is None
            text_body = json.dumps(json_body)

        # copy
        rheaders = dict(self._headers)
        # expand
        if headers is not None:
            rheaders.update(headers)
        # trim
        if no_auth_header:
            try:
                del rheaders['Authorization']
            except KeyError:
                pass

        url = slash_join(self.base_url, path)
        try:
            r = self._session.request(method=method,
                                      url=url,
                                      headers=rheaders,
                                      params=params,
                                      data=text_body,
                                      verify=self._verify)
        except requests.Timeout as e:
            raise exc.TimeoutError(*e.args)
        except requests.ConnectionError as e:
            raise exc.ConnectionError(*e.args)
        except requests.RequestException as e:
            raise exc.NetworkError(*e.args)
        if 200 <= r.status_code < 400:
            if response_class is None:
                return self.default_response_class(r)
            else:
                return response_class(r)
        raise self.error_class(r)


def slash_join(a, b):
    """
    Join a and b with a single slash, regardless of whether they already
    contain a trailing/leading slash or neither.
    """
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
