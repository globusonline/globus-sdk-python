OAuth Flows
-----------

If you want to get started doing OAuth2 flows, you should read the
`tutorial <oauth/tutorial.html>`_.

Flow Managers
~~~~~~~~~~~~~

These objects represent in-progress OAuth2 authentication flows.
Most typically, you should not use these objects, but rather rely on the
:class:`globus_sdk.AuthClient` object to manage one of these for you through
its ``oauth2_*`` methods.

All Flow Managers inherit from the 
:class:`GlobusOAuthFlowManager \
<globus_sdk.auth.oauth_flow_manager.GlobusOAuthFlowManager>` abstract class.
They are a combination of a store for OAuth2 parameters specific to the
authentication method you are using and methods which act upon those parameters.

.. autoclass:: globus_sdk.auth.oauth_flow_manager.GlobusOAuthFlowManager
   :members:
   :show-inheritance:

.. autoclass:: globus_sdk.auth.GlobusNativeAppFlowManager
   :members:
   :show-inheritance:

