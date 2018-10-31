import threading

import httpretty
import pytest
import requests
from six.moves.urllib.parse import urlencode

from globus_sdk.exc import LocalServerError
from globus_sdk.utils.local_server import start_local_server


class LocalServerTester:
    def __init__(self):
        self.server_response = None

    def _wait_for_code(self, server):
        try:
            self.server_response = server.wait_for_code()
        except Exception as e:
            self.server_response = e

    def test(self, response_params):
        """
        Start a local server to wait for an 'auth_code'. Usually the user's
        browser will redirect to this location, but in this case the user is
        mocked with a separate request in another thread.

        Waits for threads to complete and returns the local_server response.
        """
        with start_local_server() as server:
            thread = threading.Thread(target=self._wait_for_code, args=(server,))
            thread.start()
            host, port = server.server_address
            url = "http://{}:{}/?{}".format(
                "127.0.0.1", port, urlencode(response_params)
            )
            requests.get(url)
            thread.join()
            return self.server_response


@pytest.yield_fixture
def test_server():
    httpretty.disable()
    yield LocalServerTester()
    httpretty.enable()


def test_local_server_with_auth_code(test_server):
    MOCK_AUTH_CODE = (
        "V2UgY2FuJ3Qgd2FpdCBmb3IgY29kZXMgZm9yZXZlci4g"
        "V2VsbCwgd2UgY2FuIGJ1dCBJIGRvbid0IHdhbnQgdG8u"
    )
    assert test_server.test({"code": MOCK_AUTH_CODE}) == MOCK_AUTH_CODE


def test_local_server_with_error(test_server):
    response = test_server.test({"error": "bad things happened"})
    assert isinstance(response, LocalServerError)
