import time

from globus_sdk.transfer.response.base import TransferResponse


class ActivationRequirementsResponse(TransferResponse):
    """
    Response class for Activation Requirements responses.

    All Activation Requirements documents refer to a specific Endpoint, from
    whence they were acquired. References to "the Endpoint" implicitly refer to
    that originating Endpoint, and not to some other Endpoint.

    **External Documentation**

    See
    `Activation Requirements Document\
    <https://docs.globus.org/api/transfer/endpoint_activation/#activation_requirements_document>`_
    in the API documentation for details.
    """
    def __init__(self, *args, **kwargs):
        TransferResponse.__init__(self, *args, **kwargs)

        # at initialization time, capture expires_in and convert to an absolute
        # timestamp -- otherwise, the time between receiving the response and
        # querying its status will start to matter
        if self["expires_in"] == -1:
            # expires_in=-1 is the "infinite lifetime" case
            self.expires_at = None
        else:
            self.expires_at = int(time.time() + self["expires_in"])

    @property
    def supports_auto_activation(self):
        r"""
        Check if the document lists Auto-Activation as an available type of
        activation.
        Typically good to use when you need to catch endpoints that require web
        activation before proceeding.

        >>> endpoint_id = "..."
        >>> tc = TransferClient(...)
        >>> reqs_doc = tc.endpoint_get_activation_requirements(endpoint_id)
        >>> if not reqs_doc.supports_auto_activation:
        >>>     # use `from __future__ import print_function` in py2
        >>>     print(("This endpoint requires web activation. "
        >>>            "Please login and activate the endpoint here:\n"
        >>>            "https://www.globus.org/app/endpoints/{0}/activate")
        >>>           .format(endpoint_id), file=sys.stderr)
        >>>     # py3 calls it `input()` in py2, use `raw_input()`
        >>>     input("Please Hit Enter When You Are Done")

        :rtype: ``bool``
        """
        return self["auto_activation_supported"]

    @property
    def supports_web_activation(self):
        """
        Check if the document lists known types of activation that can be done
        through the web. If this returns ``False``, it means that the endpoint
        is of a highly unusual type, and you should directly inspect the
        response's ``data`` attribute to see what is required. Sending users to
        the web page for activation is also a fairly safe action to take.
        Note that ``ActivationRequirementsResponse.supports_auto_activation``
        directly implies
        ``ActivationRequirementsResponse.supports_web_activation``, so these
        are *not* exclusive.

        For example,

        >>> tc = TransferClient(...)
        >>> reqs_doc = tc.endpoint_get_activation_requirements(...)
        >>> if not reqs_doc.supports_web_activation:
        >>>     # use `from __future__ import print_function` in py2
        >>>     print("Highly unusual endpoint. " +
        >>>           "Cannot webactivate. Raw doc: " +
        >>>           str(reqs_doc), file=sys.stderr)
        >>>     print("Sending user to web anyway, just in case.",
        >>>           file=sys.stderr)
        >>> ...

        :rtype: ``bool``
        """
        return (self.supports_auto_activation or
                self["oauth_server"] is not None or
                any(x for x in self["DATA"]
                    if x['type'] in ('myproxy', 'delegate_myproxy')))

    def active_until(self, time_seconds, relative_time=True):
        """
        Check if the Endpoint will be active until some time in the future,
        given as an integer number of seconds.
        When ``relative_time=False``, the ``time_seconds`` is interpreted as a
        POSIX timestamp.

        This supports queries using both relative and absolute timestamps to
        better support a wide range of use cases. For example, if I have a task
        that I know will typically take N seconds, and I want an M second
        safety margin:

        >>> num_secs_allowed = N + M
        >>> tc = TransferClient(...)
        >>> reqs_doc = tc.endpoint_get_activation_requirements(...)
        >>> if not reqs_doc.active_until(num_secs_allowed):
        >>>     raise Exception("Endpoint won't be active long enough")
        >>> ...

        or, alternatively, if I know that the endpoint must be active until
        October 18th, 2016 for my tasks to complete:

        >>> oct18_2016 = 1476803436
        >>> tc = TransferClient(...)
        >>> reqs_doc = tc.endpoint_get_activation_requirements(...)
        >>> if not reqs_doc.active_until(oct18_2016, relative_time=False):
        >>>     raise Exception("Endpoint won't be active long enough")
        >>> ...

        **Parameters**

          ``time_seconds``
            Integer number of seconds into the future.

          ``relative_time``
            Defaults to True. When False, ``time_seconds`` is treated as a
            POSIX timestamp (i.e. seconds since epoch as an integer) instead of
            its ordinary behavior.

        :rtype: ``bool``
        """
        # inactive endpoint
        if not self["activated"]:
            return False
        # infinite activation period
        if self.expires_at is None:
            return True

        if relative_time:
            return (time.time() + time_seconds) < self.expires_at
        else:
            return time_seconds < self.expires_at

    @property
    def always_activated(self):
        """
        Returns True if the endpoint activation never expires
        (e.g. shared endpoints, globus connect personal endpoints).

        :rtype: ``bool``
        """
        return self["expires_in"] == -1
