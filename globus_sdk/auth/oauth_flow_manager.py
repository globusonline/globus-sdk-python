class GlobusOAuthFlowManager(object):
    """
    An abstract class definition that defines the interface for the Flow
    Managers for Globus Auth.
    Flow Managers are really just bundles of parameters to Globus Auth's OAuth2
    mechanisms, along with some useful utility methods.
    Primarily they can be used as a simple way of tracking small amounts of
    state in your application as it leverages Globus Auth for authentication.

    For sophisticated use cases, the provided Flow Managers will *NOT* be
    sufficient, but you should consider the provided objects a model.

    This way of managing OAuth2 flows is inspired by
    `oauth2client <https://github.com/google/oauth2client>`_. However, because
    ``oauth2client`` has an uncertain future (as of 2016-08-31), and we would
    have to wrap it in order to provide a clean API surface anyway, we
    implement our own set of Flow objects.
    """
    def get_authorize_url(self):
        """
        This method consumes no arguments or keyword arguments, and produces a
        string URL for the Authorize Step of a 3-legged OAuth2 flow.
        Most typically, this is the first step of the flow, and the user may be
        redirected to the URL or provided with a link.

        The authorize_url may be (usually is) parameterized over attributes of
        the specific flow manager instance which is generating it.

        :rtype: ``string``
        """
        raise NotImplementedError(
            '{0} does not implement get_authorize_url()'.format(type(self)))

    def exchange_code_for_tokens(self, auth_code):
        """
        This method takes an auth_code and produces a dict-like
        object containing one or more tokens.
        Most typically, this is the second step of the flow, and consumes the
        auth_code that was sent to a redirect URI used in the authorize step.

        The exchange process may be parameterized over attributes of the
        specific flow manager instance which is generating it.

        :param auth_code: The authorization code which was produced from the
                          authorization flow. In the default flow, this is
        :rtype: ``dict`` or ``dict``-like
        """
        raise NotImplementedError(
            '{0} does not implement exchange_code_for_tokens()'
            .format(type(self)))
