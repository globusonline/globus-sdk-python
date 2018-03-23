Exceptions
==========

All Globus SDK errors inherit from ``GlobusError``, and all SDK error classes
are importable from ``globus_sdk``.

You can therefore capture *all* errors thrown by the SDK by looking for
``GlobusError``, as in::

    import logging
    from globus_sdk import TransferClient, GlobusError

    try:
        tc = TransferClient(...)
        # search with no parameters will throw an exception
        eps = tc.endpoint_search()
    except GlobusError:
        logging.exception("Globus Error!")
        raise

In most cases, it's best to look for specific subclasses of ``GlobusError``.
For example, to write code which is distinguishes between network failures and
unexpected API conditions, you'll want to look for ``NetworkError`` and
``GlobusAPIError``::

    import logging
    from globus_sdk import (TransferClient,
                            GlobusError, GlobusAPIError, NetworkError)

    try:
        tc = TransferClient(...)

        eps = tc.endpoint_search(filter_fulltext="myendpointsearch")

        for ep in eps:
            print(ep["display_name"])

        ...
    except GlobusAPIError as e:
        # Error response from the REST service, check the code and message for
        # details.
        logging.error(("Got a Globus API Error\n"
                       "Error Code: {0}\n"
                       "Error Message: {0}").format(e.code, e.message))
        raise e
    except NetworkError:
        logging.error(("Network Failure. "
                       "Possibly a firewall or connectivity issue"))
        raise
    except GlobusError:
        logging.exception("Totally unexpected GlobusError!")
        raise
    else:
        ...

Of course, if you want to learn more information about the response, you should
inspect it more than this.

All errors raised by the SDK should be instances of ``GlobusError``.
Malformed calls to Globus SDK methods typically raise ``GlobusSDKUsageError``,
but, in rare cases, may raise standard python exceptions (``ValueError``,
``OSError``, etc.)


Error Classes
-------------

.. autoclass:: globus_sdk.GlobusError
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.GlobusSDKUsageError
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.GlobusAPIError
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.NetworkError
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.GlobusConnectionError
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.GlobusTimeoutError
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.GlobusConnectionTimeoutError
   :members:
   :show-inheritance:
