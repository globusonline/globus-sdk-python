.. _examples_three_legged_oauth_login:

Three Legged OAuth with Flask
-----------------------------

This type of authorization is used for web login with a server-side
application. For example, a Django app or other application server handles
requests.

This example uses Flask, but should be easily portable to other application
frameworks.


Components
~~~~~~~~~~

There are two components to this application: login and logout.

Login sends a user to Globus Auth to get credentials, and then may act on the
user's behalf.
Logout invalidates server-side credentials, so that the application may no
longer take actions for the user, and the client-side session,
allowing for a fresh login if desired.

Register an App
~~~~~~~~~~~~~~~

In order to complete an OAuth2 flow to get tokens, you must have a client
definition registered with Globus Auth.
To do so, follow the relevant documentation for the
`Globus Auth Service <https://docs.globus.org/api/auth/>`_ or go directly to
`developers.globus.org <https://developers.globus.org/>`_ to do the
registration.

Make sure that the "Native App" checkbox is unchecked, and list
``http://localhost:5000/login`` in the "Redirect URIs".

Set the Scopes to ``openid``, ``profile``, ``email``,
``urn:globus:auth:scope:transfer.api.globus.org:all``.

On the projects page, expand the client description and click "Generate
Secret".
Save the resulting secret a file named ``example_app.conf``, along with the client ID:

.. code-block:: python

    SERVER_NAME = 'localhost:5000'
    # this is the session secret, used to protect the Flask session. You should
    # use a longer secret string known only to your application
    # details are beyond the scope of this example
    SECRET_KEY = 'abc123!'

    APP_CLIENT_ID = '<CLIENT_ID>'
    APP_CLIENT_SECRET = '<CLIENT_SECRET>'

Shared Utilities
~~~~~~~~~~~~~~~~

Some pieces that are of use for both parts of this flow.

First, you'll need to install ``Flask`` and the ``globus-sdk``.
Assuming you want to do so into a fresh virtualenv:

.. code-block:: bash

    $ virtualenv example-venv
    ...
    $ source example-venv/bin/activate
    $ pip install Flask==0.11.1 globus-sdk
    ...

You'll also want a shared function for loading the SDK ``AuthClient`` which
represents your application, as you'll need it in a couple of places. Create
it, along with the defintiion for your Flask app, in ``example_app.py``:

.. code-block:: python

    from flask import Flask, url_for, session, redirect, request
    import globus_sdk

    app = Flask(__name__)
    app.config.from_pyfile('example_app.conf')


    # actually run the app if this is called as a script
    if __name__ == '__main__':
        app.run()


    def load_app_client():
        return globus_sdk.ConfidentialAppAuthClient(
            app.config['APP_CLIENT_ID'], app.config['APP_CLIENT_SECRET'])

Login
~~~~~

Let's add login functionality to the end of ``example_app.py``, along with a
basic index page:

.. code-block:: python

    @app.route('/')
    def index():
        """
        This could be any page you like, rendered by Flask.
        For this simple example, it will either redirect you to login, or print
        a simple message.
        """
        if not session.get('is_authenticated'):
            return redirect(url_for('login'))
        return "You are successfully logged in!"

    @app.route('/login')
    def login():
        """
        Login via Globus Auth.
        May be invoked in one of two scenarios:

          1. Login is starting, no state in Globus Auth yet
          2. Returning to application during login, already have short-lived
             code from Globus Auth to exchange for tokens, encoded in a query
             param
        """
        # the redirect URI, as a complete URI (not relative path)
        redirect_uri = url_for('login', _external=True)

        client = load_app_client()
        client.oauth2_start_flow(redirect_uri)

        # If there's no "code" query string parameter, we're in this route
        # starting a Globus Auth login flow.
        # Redirect out to Globus Auth
        if 'code' not in request.args:
            auth_uri = client.oauth2_get_authorize_url()
            return redirect(auth_uri)
        # If we do have a "code" param, we're coming back from Globus Auth
        # and can start the process of exchanging an auth code for a token.
        else:
            code = request.args.get('code')
            tokens = client.oauth2_exchange_code_for_tokens(code)

            # store the resulting tokens in the session
            session.update(
                tokens=tokens.by_resource_server,
                is_authenticated=True
            )
            return redirect(url_for('index'))

Logout
~~~~~~

Logout is very simple -- it's just a matter of cleaning up the session. It does
the added work of cleaning up any tokens you fetched by invalidating them in
Globus Auth beforehand:

.. code-block:: python

    @app.route('/logout')
    def logout():
        """
        - Revoke the tokens with Globus Auth.
        - Destroy the session state.
        - Redirect the user to the Globus Auth logout page.
        """
        client = load_app_client()

        # Revoke the tokens with Globus Auth
        for token in (token_info['access_token']
                      for token_info in session['tokens'].values()):
            client.oauth2_revoke_token(token)

        # Destroy the session state
        session.clear()

        # the return redirection location to give to Globus AUth
        redirect_uri = url_for('index', _external=True)

        # build the logout URI with query params
        # there is no tool to help build this (yet!)
        globus_logout_url = (
            'https://auth.globus.org/v2/web/logout' +
            '?client={0}'.format(app.config['PORTAL_CLIENT_ID']) +
            '&redirect_uri={0}'.format(redirect_uri) +
            '&redirect_name=Globus Example App')

        # Redirect the user to the Globus Auth logout page
        return redirect(globus_logout_url)


Using the Tokens
~~~~~~~~~~~~~~~~

Using the tokens thus acquired is a simple matter of pulling them out of the
session and putting one into an ``AccessTokenAuthorizer``.
For example, one might do the following:

.. code-block:: python

    authorizer = globus_sdk.AccessTokenAuthorizer(
        session['tokens']['transfer.api.globus.org']['access_token'])
    transfer_client = globus_sdk.TransferClient(authorizer=authorizer)

    print("Endpoints belonging to the current logged-in user:")
    for ep in transfer_client.endpoint_search(filter_scope="my-endpoints"):
        print("[{0}] {1}".format(ep["id"], ep["display_name"]))
