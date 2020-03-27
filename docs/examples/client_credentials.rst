Client Credentials Authentication
---------------------------------

This is an example of the use of the Globus SDK to carry out an OAuth2
Client Credentials Authentication flow.

The goal here is to have an application authenticate in Globus Auth directly,
as itself.
Unlike many other OAuth2 flows, the application does not act on behalf of a
user, but on its own behalf.

This flow is suitable for automated cases in which an application, even one as
simple as a ``cron`` job, makes use of Globus outside of the context of a
specific end-user interaction.

Get a Client
~~~~~~~~~~~~

In order to complete an OAuth2 flow to get tokens, you must have a client
definition registered with Globus Auth.
To do so, follow the relevant documentation for the
`Globus Auth Service <https://docs.globus.org/api/auth/>`_ or go directly to
`developers.globus.org <https://developers.globus.org/>`_ to do the
registration.

During registration, make sure that the "Native App" checkbox is unchecked.
You will typically want your scopes to be ``openid``, ``profile``, ``email``,
and ``urn:globus:auth:scope:transfer.api.globus.org:all``.

Once your client is created, expand it on the Projects page and click "Generate
Secret". Save the secret in a secure location accessible from your code.

Do the Flow
~~~~~~~~~~~

You should specifically use the :class:`ConfidentialAppAuthClient
<globus_sdk.ConfidentialAppAuthClient>` type of ``AuthClient``, as it has been
customized to handle this flow.

The shortest version of the flow looks like this:

.. code-block:: python

    import globus_sdk

    # you must have a client ID
    CLIENT_ID = '...'
    # the secret, loaded from wherever you store it
    CLIENT_SECRET = '...'

    client = globus_sdk.ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)
    token_response = client.oauth2_client_credentials_tokens()

    # the useful values that you want at the end of this
    globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
    globus_auth_token = globus_auth_data['access_token']
    globus_transfer_token = globus_transfer_data['access_token']


Use the Resulting Tokens
~~~~~~~~~~~~~~~~~~~~~~~~

The Client Credentials Grant will only produce Access Tokens, not Refresh
Tokens, so you should pass its results directly to the :class:`AccessTokenAuthorizer
<globus_sdk.AccessTokenAuthorizer>`.

For example, after running the code above,

.. code-block:: python

    authorizer = globus_sdk.AccessTokenAuthorizer(globus_transfer_token)
    tc = globus_sdk.TransferClient(authorizer=authorizer)
    print("Endpoints Belonging to {}@clients.auth.globus.org:"
          .format(CLIENT_ID))
    for ep in tc.endpoint_search(filter_scope="my-endpoints"):
        print("[{}] {}".format(ep["id"], ep["display_name"]))

Note that we're doing a search for "my endpoints", but we refer to the results
as belonging to ``<CLIENT_ID>@clients.auth.globus.org``. The "current user" is
not any human user, but the client itself.

Handling Token Expiration
~~~~~~~~~~~~~~~~~~~~~~~~~

When you get access tokens, you also get their expiration time in seconds.
You can inspect the ``globus_transfer_data`` and ``globus_auth_data``
structures in the example to see.

Tokens should have a long enough lifetime for any short-running operations
(less than a day).

When your tokens are expired, you should just request new ones by making
another Client Credentials request.
Depending on your needs, you may need to track the expiration times along with
your tokens.

Using ClientCredentialsAuthorizer
---------------------------------

The SDK also provides a specialized Authorizer which can be used to
automatically handle token expiration.

Use it like so:

.. code-block:: python

    import globus_sdk

    # you must have a client ID
    CLIENT_ID = '...'
    # the secret, loaded from wherever you store it
    CLIENT_SECRET = '...'

    confidential_client = globus_sdk.ConfidentialAppAuthClient(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    scopes = "urn:globus:auth:scope:transfer.api.globus.org:all"
    cc_authorizer = globus_sdk.ClientCredentialsAuthorizer(
        confidential_client, scopes)
    # create a new client
    transfer_client = globus_sdk.TransferClient(authorizer=cc_authorizer)

    # usage is still the same
    print("Endpoints Belonging to {}@clients.auth.globus.org:"
          .format(CLIENT_ID))
    for ep in tc.endpoint_search(filter_scope="my-endpoints"):
        print("[{}] {}".format(ep["id"], ep["display_name"]))
