Responses
=========

All method return values for Globus SDK Clients are ``GlobusResponse``
objects.
Some ``GlobusResponse`` objects are iterables.
In those cases, their contents will also be ``GlobusResponse`` objects.

To customize client methods with additional detail, the SDK uses subclasses of
``GlobusResponse``.
For example the ``GlobusHTTPResponse`` attaches HTTP response information.

Response Classes
----------------

.. autoclass:: globus_sdk.response.GlobusResponse
   :members:

.. autoclass:: globus_sdk.response.GlobusHTTPResponse
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.transfer.response.TransferResponse
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.transfer.response.IterableTransferResponse
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.auth.token_response.GlobusOAuthTokenResponse
   :members:
   :show-inheritance:
