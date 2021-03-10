import json
import typing

from globus_sdk.tokenstorage.base import FileAdapter
from globus_sdk.version import __version__

if typing.TYPE_CHECKING:  # conditional imports reduce the risk of dependency cycles
    from globus_sdk.auth import OAuthTokenResponse


class SimpleJSONFileAdapter(FileAdapter):
    """
    :param filename: the name of the file to write to and read from
    :param resource_server: the resource server name for tokens to look up
                            in a token response object
    :param scopes: a list of scope names for tokens to look up in a token
                   response object

    A storage adapter for storing tokens in JSON files.
    Callers must provide exactly one of ``resource_server`` and ``scopes``
    """

    def __init__(
        self,
        filename: str,
        resource_server: typing.Optional[str] = None,
        scopes: typing.Optional[str] = None,
    ):
        if resource_server and scopes:
            raise ValueError("cannot take both resource_server and scopes")
        elif not resource_server and not scopes:
            raise ValueError("you must pass resource_server or scopes")

        self.filename = filename
        self.resource_server = resource_server
        self.scopes = scopes

    def _lookup_data_from_response(
        self, token_response: "OAuthTokenResponse"
    ) -> typing.Dict:
        """
        Given a token response, extract the token data for the configured
        scopes or resource servers of this adapter
        """
        # extract desired data and copy as a new dict
        if self.resource_server:
            return dict(token_response.by_resource_server[self.resource_server])
        elif self.scopes:
            # NOTE: this can fail if `self.scopes` isn't for exactly one
            # resource server, but then the failure will simply propagate up
            return dict(token_response.by_scopes[self.scopes])
        else:
            raise NotImplementedError("neither resource_server nor scopes are set")

    def store(self, token_response: "OAuthTokenResponse"):
        """
        By default, ``self.on_refresh`` is just an alias for this function.

        Given a token response, extract the token data for the configured
        scopes or resource servers of this file adapter and write it to
        ``self.filename`` as JSON data.
        Additionally will write the version of ``globus_sdk_tokenstorage``
        which was in use.

        Under the assumption that this may be running on a system with multiple
        local users, this sets the umask such that only the owner of the
        resulting file can read or write it.
        """
        to_write = self._lookup_data_from_response(token_response)

        # deny rwx to Group and World, exec to User
        with self.user_only_umask():
            # add the version as an attribute at the top level of the JSON
            # structure
            to_write["globus-sdk.version"] = __version__
            with open(self.filename, "w") as f:
                json.dump(to_write, f)

    def read_as_dict(self) -> typing.Dict:
        """
        Load the config file contents as JSON and return the resulting dict
        object.

        Although the whole token response is passed in for ``self.store``, this
        will only return the token data for the particular scopes or resource
        server for which this File Adapter is configured.
        """
        with open(self.filename) as f:
            val = json.load(f)
        if not isinstance(val, dict):
            raise ValueError("reading from json file got non-dict data")
        return val
