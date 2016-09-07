Resouce Servers and Scopes
==========================

What are Resource Servers, and how do they interact with scopes?

If you look at a :class:`GlobusOAuthTokenResponse
<globus_sdk.auth.token_response.GlobusOAuthTokenResponse>`, you will notice
that it organizes information under Resource Servers, including one access
token (and optionally one refresh token) per Resource Server.
This can appear confusing, especially as the Resource Servers in this response
do not map one-to-one onto the scopes that your application requested.

This is a brief description Resource Servers to make sense of this response.

Short-Short Version
-------------------

Resource Servers are just the OAuth2 name for services which use scopes on
tokens to control access to their resources.

Less-Short Version
------------------

When you request tokens, you do so with a set of scopes.
Our default set consists of
``openid profile email urn:globus:auth:scope:transfer.api.globus.org:all``.
That means you can get OpenID Connect data in general, profile data, email
address, and access to Globus Transfer resources (in that order).

However, for those four scopes, there aren't four distinct services -- there
are only two.
``openid``, ``profile``, and ``email`` all correspond to the service at
``auth.globus.org`` (Globus Auth) while
``urn:globus:auth:scope:transfer.api.globus.org:all`` corresponds to
``transfer.api.globus.org`` (Globus Transfer).

As a result, we don't get four tokens for our four scopes -- we get two tokens,
one for the first three scopes, and one for the last scope.
Those tokens can be organized better by their relevant Resource Server than by
their scope names, which is why we use the ``token_response.by_resource_server``
description.

Why Not Just One Token?
-----------------------

The reason for separate tokens at all (as opposed to one token with all four
scopes) is to limit the exposure of tokens for different services.

As a motivating example, consider a new service registered as Resource Server
in Globus belonging to another organization -- ``serv.example.com``.
``serv.example.com`` should not see tokens scoped for Globus Transfer, and
Globus Transfer shouldn't see tokens scoped for ``serv.example.com``.

Using a single token for all Resource Servers would make isolating services in
this way impossible.
