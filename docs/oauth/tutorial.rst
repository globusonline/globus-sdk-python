Globus OAuth2 SDK Tutorial
--------------------------

This is a tutorial in the use of the Globus SDK to carry out an OAuth2
Authentication flow.

The goal here is to have a user authenticate in Globus Auth, and for the SDK
to procure tokens which may be used to authenticate SDK calls against various
services for that user.

Get a Client
~~~~~~~~~~~~

In order to complete an OAuth2 flow to get tokens, you must have a client
definition registered with Globus Auth.
To do so, follow the relevant documentation for the
`Globus Auth Service <https://docs.globus.org/api/auth/>`_.

(Note: As of 2016-08-31, registering a client requires an out of band process
with the Globus Team. This document assumes that you already have one)


Native App Grant Explained
~~~~~~~~~~~~~~~~~~~~~~~~~~

Right now, the only flow that the SDK supports is the "Native App Grant", which
is designed to handle the case of an application which cannot protect a client
secret.
These applications need to engage in an exchange of temporary credentials that
is based on the 3-legged OAuth flow.

The basic flow can be described as the following procedure:

1. The application generates a secret
2. The application directs the user to authenticate at the Globus Auth
   ``authorize URL``, with a hash of the secret. Usually the user is given a
   link to the ``authorize URL``
3. The user follows the link and logs in to any Globus Auth supported system*
4. Globus Auth, after a successful login, sends an ``auth_code`` back to the
   user or directly to the application (the user may copy-paste the code back
   to the application)
5. The application sends the ``auth_code`` and the unhashed secret from (1) to
   the server in exchange for a set of tokens

* Globus Auth allows users to login with a variety of institutional accounts,
  Google accounts, and with free "Globus ID" accounts. By default, any of these
  are allowed, but an application can also specify that a certain type of
  account be used by the user. Full details exceed the scope of this document.


The key goal of this flow is to have the user perform authentication via a web
browser (which can therefore interface with a wide variety of login providers),
but never expose the tokens, which are long-lived credentials, to the browser.
The only pieces of software that ever handle tokens are the application and
Globus Auth -- all other credentials used are limited lifetime.


Native App Flow on AuthClient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to copy-paste an example, you'll need at least a ``client_id`` for
your ``AuthClient`` object.
The shortest version of this flow looks like this:

.. code-block:: python

    import globus-sdk
    # include your client_id, of course
    client = globus_sdk.AuthClient(client_id=...)
    client.oauth2_native_app_start_flow()

    authorize_url = client.oauth2_get_authorize_url()
    print('Please go to this URL and login: {0}'.format(authorize_url))

    # or just input() on python3
    auth_code = raw_input(
        'Please enter the code you get after login here: ').strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # the useful values that you want at the end of this
    globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
    globus_auth_token = globus_auth_data['access_token']
    globus_transfer_token = globus_transfer_data['access_token']


Native App Flow in Greater Detail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's break down that super-condensed example a bit.

The first step is to create your ``AuthClient`` object to manage the Native App
OAuth2 flow.

.. code-block:: python

    import globus_sdk
    # pass in the client ID for your application, as registered in Globus Auth
    # or, you can omit it and run `client.set_client_id(...)` later
    client = globus_sdk.AuthClient(client_id=...)

Your ``client`` can only be used to run a single flow at a time.
It must include the client ID, as that will be used in several steps of the
OAuth2 flow.

Determine your ``requested_scopes``, ``redirect_uri``, and whether or not you
want ``refresh_tokens`` enabled.
A brief walkthrough of these variables:

- ``requested_scopes`` are the set of Globus Auth scopes which you are
  requesting. By default, this will be set to request access to the full
  Globus Transfer service and to get a number of standard OpenID Connect
  scopes. Unless you know precisely what you want in this field, leave it on
  its default value by not specifying it.

- ``redirect_uri`` is for use when you have a specific webpage or local URI
  where you want to handle the ``auth_code`` sent from Globus Auth. By default,
  it's the page in Globus Auth which displays the ``auth_code`` for copy-paste

- ``refresh_tokens`` is a boolean. When False, the flow will terminate with a
  collection of Access Tokens, which are simple limited lifetime credentials
  for accessing services. When True, the flow will terminate not only with the
  Access Tokens, but additionally with a set of Refresh Tokens which can be
  used **indefinitely** to request new Access Tokens. (They may expire if they
  are unused for a long period of time, but theoretically have an infinite
  lifetime.) The default is False.

Okay, now you want to pass those values into the Native App Flow start method.
Maybe you're only specifying ``refresh_tokens`` explicitly:

.. code-block:: python

    client.oauth2_native_app_start_flow(refresh_tokens=True)

With the Native App flow started, you can generate an ``authorize URL`` with
its various encoded parameters.
If you attempt this step without starting a flow, you'll get errors, as the
``AuthClient`` doesn't know which specific OAuth2 flow you want to use.

.. code-block:: python

    # no parameters are necessary -- you passed them all when initializing the
    # flow
    authorize_url = client.oauth2_get_authorize_url()

    # you can choose to do this by another method, but the simplest way is to
    # print and tell the user to go here
    print('Please go to this URL and login: {0}'.format(authorize_url))

This is also a good stage at which to tell users what to do with the resulting
``auth_code``, if you are using the default ``redirect_uri`` value:

.. code-block:: python

    auth_code = raw_input(
        'Please enter the code you receive after login here: ').strip()

Now that you have the ``auth_code``, you can exchange it for set of tokens::

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

That ``token_response`` is a :class:`GlobusOAuthTokenResponse
<globus_sdk.auth.token_response.GlobusOAuthTokenResponse>`, so it will be
easiest to work with the response reformatted to be organized by Resource
Server.

.. code-block:: python

    globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
    globus_auth_token = globus_auth_data['access_token']
    globus_transfer_token = globus_transfer_data['access_token']

What's up with that funky format though? And what are Resource Servers?
More on that can be found `here <resource_servers.html>`_.

For now, let's move forward with that transfer token. It's good to go:

.. code-block:: python

    transfer_client = globus_sdk.TransferClient(token=globus_transfer_token)
    # do something with the token
    print(transfer_client.task_list())

If you included ``refresh_tokens=True`` earlier, you would have refresh tokens
available in:

.. code-block:: python

    globus_auth_data['refresh_token']
    globus_transfer_data['refresh_token']


Flow Managers
~~~~~~~~~~~~~

We recommend that, until you are comfortable with the steps of OAuth2 flows,
you start by using the above technique.
If your use case is too complex for the ``AuthClient`` methods, you may find it
beneficial to explicitly use the underlying `Flow Manager <flows.html>`_
objects.
