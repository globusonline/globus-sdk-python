.. _tutorial:

SDK Tutorial
============

This is a tutorial in the use of the Globus SDK. It takes you through a simple
step-by-step flow for registering your application, getting tokens, and using
them with our service.

These are the steps we will take:

#. :ref:`Get a Client <tutorial_step1>`
#. :ref:`Get and Save Client ID <tutorial_step2>`
#. :ref:`Get Some Access Tokens! <tutorial_step3>`
#. :ref:`Use Your Tokens, Talk to the Service <tutorial_step4>`

That should be enough to get you up and started.
You can also proceed to the :ref:`Advanced Tutorial <advanced_tutorial>` steps
to dig deeper into the SDK.

.. _tutorial_step1:

Step 1: Get a Client
--------------------

In order to complete an OAuth2 flow to get tokens, you must have a client or
"app" definition registered with Globus.

Navigate to the `Developer Site <https://developers.globus.org>`_ and select
"Register your app with Globus."
You will be prompted to login -- do so with the account you wish to use as your
app's administrator.

When prompted, create a Project named "SDK Tutorial Project".
Projects let you share the administrative burden of a collection of apps, but
we won't be sharing the SDK Tutorial Project.

In the "Add..." menu for "SDK Tutorial Project", select "Add new app".

Enter the following pieces of information:

- **App Name**: "SDK Tutorial App"
- **Scopes**: "openid", "profile", "email",
  "urn:globus:auth:scope:transfer.api.globus.org:all"
- **Redirects**: https://auth.globus.org/v2/web/auth-code
- **Required Identity Provider**: <Leave Unchecked>
- **Privacy Policy**: <Leave Blank>
- **Terms & Conditions**: <Leave Blank>
- **Native App**: Check this Box

and click "Create App".

.. _tutorial_step2:

Step 2: Get and Save Client ID
------------------------------

On the "Apps" screen you should now see all of your Projects, probably just
"SDK Tutorial Project", and all of the Apps they contain, probably just "SDK
Tutorial App".
Expand the dropdown for the tutorial App, and you should see an array of
attributes of your client, including the ones we specified in Step 1, and a
bunch of new things.

We want to get the Client ID from this screen.
Feel free to think of this as your App's "username".
You can hardcode it into scripts, store it in a config file, or even put it
into a database.
It's non-secure information and you can treat it as such.

In the rest of the tutorial we will assume in all code samples that it is
available in the variable, ``CLIENT_ID``.

.. _tutorial_step3:

Step 3: Get Some Access Tokens!
-------------------------------

Talking to Globus Services as a user requires that you authenticate to your new
App and get it Tokens, credentials proving that you logged into it and gave it
permission to access the service.

No need to worry about creating your own login pages and such -- for this type
of app, Globus provides all of that for you.
Run the following code sample to get your Access Tokens:

.. code-block:: python

    import globus_sdk

    CLIENT_ID = '<YOUR_ID_HERE>'

    client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
    client.oauth2_start_flow()

    authorize_url = client.oauth2_get_authorize_url()
    print('Please go to this URL and login: {0}'.format(authorize_url))

    # this is to work on Python2 and Python3 -- you can just use raw_input() or
    # input() for your specific version
    get_input = getattr(__builtins__, 'raw_input', input)
    auth_code = get_input(
        'Please enter the code you get after login here: ').strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']

    # most specifically, you want these tokens as strings
    AUTH_TOKEN = globus_auth_data['access_token']
    TRANSFER_TOKEN = globus_transfer_data['access_token']


Managing credentials is one of the more advanced features of the SDK.
If you want to read in depth about these steps, please look through our various
:ref:`Examples <examples>`.

.. _tutorial_step4:

Step 4: Use Your Tokens, Talk to the Service
--------------------------------------------

Continuing from the example above, you have two credentials to Globus Services
on hand: the ``AUTH_TOKEN`` and the ``TRANSFER_TOKEN``.
We'll focus on the ``TRANSFER_TOKEN`` for now. It's how you authorize access to
the Globus Transfer service.

.. code-block:: python

    # a GlobusAuthorizer is an auxiliary object we use to wrap the token. In
    # more advanced scenarios, other types of GlobusAuthorizers give us
    # expressive power
    authorizer = globus_sdk.AccessTokenAuthorizer(TRANSFER_TOKEN)
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    # high level interface; provides iterators for list responses
    print("My Endpoints:")
    for ep in tc.endpoint_search(filter_scope="my-endpoints"):
        print("[{0}] {1}".format(ep["id"], ep["display_name"]))


Note that the ``TRANSFER_TOKEN`` is only valid for a limited time. You'll have
to login again when it expires.


.. _advanced_tutorial:

Advanced Tutorial
-----------------

In the first 4 steps of the Tutorial, we did a lot of hocus-pocus to procure
Access Tokens, but we didn't dive into how we are getting them (or why they
exist at all).
Not only will we talk through more detail on Access Tokens, but we'll also
explore more advanced use cases and their near-cousins, Refresh Tokens.

Advanced 1: Exploring the OAuthTokenResponse
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We powered through the OAuth2 flow in the basic tutorial.
It's worth looking closer at the token response itself, as it is of particular
interest.
This is the ultimate product of the flow, and it contains all of the
credentials that we'll want and need moving forward.

Remember:

.. code-block:: python

    client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
    client.oauth2_start_flow()

    print('Please go to this URL and login: {0}'
          .format(client.oauth2_get_authorize_url()))

    get_input = getattr(__builtins__, 'raw_input', input)
    auth_code = get_input('Please enter the code here: ').strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

Though it has a few attributes and methods, by far the most important thing
about ``token_response`` to understand is
``token_response.by_resource_server``.

Let's take a look at ``str(token_response.by_resource_server)``:

.. code-block:: python

    >>> str(token_response.by_resource_server)
    {
      "auth.globus.org": {
        "access_token": "AQBX8YvVAAAAAAADxhAtF46RxjcFuoxN1oSOmEk-hBqvOejY4imMbZlC0B8THfoFuOK9rshN6TV7I0uwf0hb",
        "scope": "openid email profile",
        "token_type": "Bearer",
        "expires_at_seconds": 1476121216,
        "refresh_token": None
      },
      "transfer.api.globus.org": {
        "access_token": "AQBX8YvVAAAAAAADxg-u9uULMyTkLw4_15ReO_f2E056wLqjAWeLP51pgakLxYmyUDfGTd4SnYCiRjFq3mnj",
        "scope": "urn:globus:auth:scope:transfer.api.globus.org:all",
        "token_type": "Bearer",
        "expires_at_seconds": 1476121286,
        "refresh_token": None
      }
    }

A token response is structured with the following info:

- Resource Servers: The services (e.x. APIs) which require Tokens. These are
  the keys, `"auth.globus.org"` and `"transfer.api.globus.org"`
- Access Tokens: Credentials you can use to talk to Resource Servers. We get
  back separate Access Tokens for each Resource Server. Importantly, this means
  that if Globus is issuing tokens to `evil.api.example.com`, you don't need to
  worry that `evil.api.example.com` will ever see tokens valid for Globus
  Transfer
- Scope: A list of activities that the Access Token is good for against the
  Resource Server. They are defined and enforced by the Resource Server.
- token_type: With what kind of authorization should the Access Token be
  used? For the foreseeable future, all Globus tokens are sent as Bearer Auth
  headers.
- expires_at_seconds: A POSIX timestamp -- the time at which the relevant
  Access Token expires and is no longer accepted by the service.
- Refresh Tokens: Credentials used to replace or "refresh" your access tokens
  when they expire. If requested, you'll get one for each Resource Server.
  Details on their usage are in the next Advanced Tutorial


Advanced 2: Refresh Tokens, Never Login Again
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Logging in to Globus through the web interface gets pretty old pretty fast.
In fact, as soon as you write your first cron job against Globus, you'll need
something better.
Enter Refresh Tokens: credentials which never expire unless revoked, and which
can be used to get new Access Tokens whenever those do expire.

Getting yourself refresh tokens to play with is actually pretty easy. Just
tweak your login flow with one argument:

.. code-block:: python

    client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
    client.oauth2_start_flow(refresh_tokens=True)

    print('Please go to this URL and login: {0}'
          .format(client.oauth2_get_authorize_url()))

    get_input = getattr(__builtins__, 'raw_input', input)
    auth_code = get_input('Please enter the code here: ').strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

If you peek at the ``token_response`` now, you'll see that the
``"refresh_token"`` fields are no longer nulled.

Now we've got a problem though: it's great to say that you can refresh tokens
whenever you want, but how do you know when to do that? And what if an Access
Token gets revoked before it's ready to expire?
It turns out that using these correctly is pretty delicate, but there is a way
forward that's pretty much painless.

Let's assume you want to do this with the ``globus_sdk.TransferClient``.

.. code-block:: python

    # let's get stuff for the Globus Transfer service
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
    # the refresh token and access token, often abbr. as RT and AT
    transfer_rt = globus_transfer_data['refresh_token']
    transfer_at = globus_transfer_data['access_token']
    expires_at_s = globus_transfer_data['expires_at_seconds']

    # Now we've got the data we need, but what do we do?
    # That "GlobusAuthorizer" from before is about to come to the rescue

    authorizer = globus_sdk.RefreshTokenAuthorizer(
        transfer_rt, client, access_token=transfer_at, expires_at=expires_at_s)

    # and try using `tc` to make TransferClient calls. Everything should just
    # work -- for days and days, months and months, even years
    tc = globus_sdk.TransferClient(authorizer=authorizer)

A couple of things to note about this: ``access_token`` and ``expires_at`` are
optional arguments to ``RefreshTokenAuthorizer``. So, if all you've got on hand
is a refresh token, it can handle the bootstrapping problem.
Also, it's good to know that the ``RefreshTokenAuthorizer`` will retry the
first call that fails with an authorization error. If the second call also
fails, it won't try anymore.

Finally, and perhaps most importantly, we must stress that you need to protect
your Refresh Tokens. They are an infinite lifetime credential to act as you,
so, like passwords, they should only be stored in secure locations.
