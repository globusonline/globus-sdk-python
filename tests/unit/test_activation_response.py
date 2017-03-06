import requests
import json
import six
import time

from globus_sdk.transfer.response import ActivationRequirementsResponse
from tests.framework import CapturedIOTestCase


class ActivationRequirementsResponseTests(CapturedIOTestCase):

    def make_response(self, activated=True, expires_in=0,
                      auto_activation_supported=True,
                      oauth_server=None, DATA=[]):
        """
        Helper for making ActivationRequirementsResponses with known fields
        """
        data = {"activated": activated, "expires_in": expires_in,
                "oauth_server": oauth_server, "DATA": DATA,
                "auto_activation_supported": auto_activation_supported}
        response = requests.Response()
        response.headers["Content-Type"] = "application/json"
        response._content = six.b(json.dumps(data))
        return ActivationRequirementsResponse(response)

    def test_expires_at(self):
        """
        Confirms expires_at is set properly by __init__
        """
        for seconds in [0, 10, 100, 1000, -10]:
            response = self.make_response(expires_in=seconds)
            expected = int(time.time()) + seconds
            # make sure within a 1 second range of expected value
            self.assertIn(response.expires_at,
                          (expected - 1, expected, expected + 1))

        # -1 marks no expiration
        response = self.make_response(expires_in=-1)
        self.assertIsNone(response.expires_at)

    def test_supports_auto_activation(self):
        """
        Gets supports_auto_activation from made responses, validates results
        """
        for value in [True, False]:
            response = self.make_response(auto_activation_supported=value)
            self.assertEqual(response.supports_auto_activation, value)

    def test_supports_web_activation(self):
        """
        Gets supports_web_activation from made responses, validates results
        """
        # true if auto_activatable,
        response = self.make_response(auto_activation_supported=True)
        self.assertTrue(response.supports_web_activation)
        # has an oauth server,
        response = self.make_response(auto_activation_supported=False,
                                      oauth_server="server")
        self.assertTrue(response.supports_web_activation)
        # or one of the other documents is myproxy or delegate_myproxy,
        response = self.make_response(auto_activation_supported=False,
                                      DATA=[{"type": "myproxy"}])
        self.assertTrue(response.supports_web_activation)
        response = self.make_response(auto_activation_supported=False,
                                      DATA=[{"type": "delegate_myproxy"}])
        self.assertTrue(response.supports_web_activation)

        # otherwise false
        response = self.make_response(auto_activation_supported=False)
        self.assertFalse(response.supports_web_activation)

    def test_active_until(self):
        """
        Calls active_until on made responses, validates results
        """
        # not active at all
        response = self.make_response(activated=False)
        self.assertFalse(response.active_until(0))

        # always active
        response = self.make_response(expires_in=-1)
        self.assertTrue(response.active_until(0))

        response = self.make_response(expires_in=10)
        # relative time
        self.assertTrue(response.active_until(5))
        self.assertFalse(response.active_until(15))
        # absolute time
        now = int(time.time())
        self.assertTrue(response.active_until(now + 5, relative_time=False))
        self.assertFalse(response.active_until(now + 15, relative_time=False))

    def test_always_activated(self):
        """
        Gets always_activated property from made responses, validates results
        """
        response = self.make_response(expires_in=-1)
        self.assertTrue(response.always_activated)

        response = self.make_response(expires_in=0)
        self.assertFalse(response.always_activated)
