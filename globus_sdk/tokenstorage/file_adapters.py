import json
import typing

from globus_sdk.auth import OAuthTokenResponse
from globus_sdk.tokenstorage.base import FileAdapter
from globus_sdk.version import __version__


class SimpleJSONFileAdapter(FileAdapter):
    """
    :param filename: the name of the file to write to and read from

    A storage adapter for storing tokens in JSON files.
    """

    # the version for the current data format used by the file adapter
    #
    # if the format needs to be changed in the future, the adapter can dispatch on
    # the declared format version in the file to decide how to handle the data
    format_version = "1.0"
    # the supported versions (data not in these versions causes an error)
    supported_versions = ("1.0",)

    def __init__(self, filename: str):
        self.filename = filename

    def _raw_load(self) -> typing.Dict:
        """
        Load the file contents as JSON and return the resulting dict
        object. If a dict is not found, raises an error.
        """
        with open(self.filename) as f:
            val = json.load(f)
        if not isinstance(val, dict):
            raise ValueError("reading from json file got non-dict data")
        return val

    def _handle_formats(self, read_data: typing.Dict) -> typing.Dict:
        """Handle older data formats supported by globus_sdk.tokenstorage

        if the data is not in a known/recognized format, this will error
        otherwise, reshape the data to the current supported format and return it
        """
        format_version = read_data.get("format_version")
        if format_version not in self.supported_versions:
            raise ValueError(
                f"cannot store data using SimpleJSONFileAdapter({self.filename} "
                "existing data file is in an unknown format "
                f"(format_version={format_version})"
            )
        if not isinstance(read_data.get("by_rs"), dict):
            raise ValueError(
                f"cannot store data using SimpleJSONFileAdapter({self.filename} "
                "existing data file is malformed"
            )
        return read_data

    def _load(self) -> typing.Dict:
        """
        Load data from the file and ensure that the data is in a modern format which can
        be handled by the rest of the adapter.

        If the file is missing, this will return a "skeleton" for new data.
        """
        try:
            data = self._raw_load()
        except FileNotFoundError:
            return {
                "by_rs": {},
                "format_version": self.format_version,
                "globus-sdk.version": __version__,
            }
        return self._handle_formats(data)

    def store(self, token_response: "OAuthTokenResponse"):
        """
        By default, ``self.on_refresh`` is just an alias for this function.

        Given a token response, extract all the token data and write it to
        ``self.filename`` as JSON data.
        Additionally will write the version of ``globus_sdk.tokenstorage``
        which was in use.

        Under the assumption that this may be running on a system with multiple
        local users, this sets the umask such that only the owner of the
        resulting file can read or write it.
        """
        to_write = self._load()

        # copy the data from the by_resource_server attribute
        #
        # if the file did not exist and we're handling the initial token response, this
        # is a full copy of all of the token data
        #
        # if the file already exists and we're handling a token refresh, we only modify
        # newly received tokens
        to_write["by_rs"].update(token_response.by_resource_server)

        # deny rwx to Group and World, exec to User
        with self.user_only_umask():
            with open(self.filename, "w") as f:
                json.dump(to_write, f)

    def get_by_resource_server(self) -> typing.Dict:
        """
        Read only the by_resource_server formatted data from the file, discarding any
        other keys.

        This returns a dict in the same format as
        ``OAuthTokenResponse.by_resource_server``
        """
        # TODO: when the Globus SDK drops support for py3.6 and py3.7, we can update
        # `_load` to return a TypedDict which guarantees that `by_rs` is a dict
        # see: https://www.python.org/dev/peps/pep-0589/
        return typing.cast(dict, self._load()["by_rs"])

    def get_token_data(self, resource_server: str) -> typing.Optional[typing.Dict]:
        return self.get_by_resource_server().get(resource_server)
