class GlobusResponse(object):
    """
    Generic response object, with a single ``data`` member.

    The most common response data is a JSON dictionary. To make
    handling this type of response as seemless as possible, the
    ``GlobusResponse`` object also supports direct dictionary item
    access, as an alias for accessing an item of the underlying
    ``data``. If ``data`` is not a dictionary, item access will raise
    ``TypeError``.

    >>> print("Response ID": r["id"]) # alias for r.data["id"]
    """
    def __init__(self, data):
        """
        ``GlobusResponse`` objects *always* wrap some kind of data to
        return to a caller. Most basic actions on a GlobusResponse are
        just ways of interacting with this data.
        """
        self._data = data

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "{0}({1!r})".format(self.__class__.__name__, self.data)

    def __getitem__(self, key):
        # force evaluation of the data property outside of the upcoming
        # try-catch so that we don't accidentally catch TypeErrors thrown
        # during the getter function itself
        data = self.data
        try:
            return data[key]
        except TypeError:
            # re-raise with an altered message -- the issue is that whatever
            # type of GlobusResponse you're working with doesn't support
            # indexing
            # "type" is ambiguous, but we don't know if it's the fault of the
            # class at large, or just a particular call's `data` property
            raise TypeError(('This type of GlobusResponse object '
                             'does not support indexing.'))

    @property
    def data(self):
        """
        Response data as a Python data structure. Usually a dict or
        list.
        """
        return self._data

    def get(self, *args, **kwargs):
        """
        ``GlobusResponse.get`` is just an alias for ``GlobusResponse.data.get``
        """
        return self.data.get(*args, **kwargs)


class GlobusHTTPResponse(GlobusResponse):
    """
    Response object that wraps an HTTP response from the underlying HTTP
    library. If the response is JSON, the parsed data will be available in
    ``data``, otherwise ``data`` will be ``None`` and ``text`` should
    be used instead.

    :ivar http_status: HTTP status code returned by the server (int)
    :ivar content_type: Content-Type header returned by the server (str)
    """
    def __init__(self, http_response):
        # the API response as some form of HTTP response object will be the
        # underlying data of an API response
        GlobusResponse.__init__(self, http_response)
        # NB: the word 'code' is confusing because we use it in the
        # error body, and status_code is not much better. http_code, or
        # http_status_code if we wanted to be really explicit, is
        # clearer, but less consistent with requests (for better and
        # worse).
        self.http_status = http_response.status_code
        self.content_type = http_response.headers["Content-Type"]

    @property
    def data(self):
        try:
            return self._data.json()
        # JSON decoding may raise a ValueError due to an invalid JSON
        # document. In the case of trying to fetch the "data" on an HTTP
        # response, this means we didn't get a JSON response. Rather than
        # letting the error bubble up, return None, as in "no data"
        # if the caller *really* wants the raw body of the response, they can
        # always use text_body
        except ValueError:
            return None

    @property
    def text(self):
        """
        The raw response data as a string.
        """
        return self._data.text
