Globus Auth / OAuth2
--------------------

Globus offers Authentication and Authorization services through an OAuth2
service, Globus Auth.

Globus Auth acts as an Authorization Server, and allows users to authenticate
with, and link together, identities from a wide range of Identity Providers.

Although the :class:`AuthClient <globus_sdk.AuthClient>` class documentation
covers normal interactions with Globus Auth, the OAuth2 flows are significantly
more complex.

This section documents the supported types of authentication and how to carry
them out, as well as providing some necessary background on various OAuth2
elements.


.. rubric:: Credentials are for Users and also for Applications

It is very important that our goal in OAuth2 is not to get credentials for an
application on its own, but rather for the application as a *client* to Globus
which is acting *on behalf of a user*.

Therefore, if you are writing an application called **foo**, and a user
**bar@example.com** is using **foo**, the credentials produced belong to the
combination of **foo** and **bar@example.com**.
The resulting credentials represent the rights and permission for **foo** to
perform actions for **bar@example.com** on systems authenticated via Globus.


.. rubric:: OAuth2 Documentation

.. toctree::
   :maxdepth: 1

   oauth/flows
   oauth/tutorial
   oauth/resource_servers
