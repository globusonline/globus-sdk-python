import requests
import json
import six
import time
import unittest
try:
    import jose
    JOSE_FLAG = True
except ImportError:
    JOSE_FLAG = False
try:
    import mock
except ImportError:
    from unittest import mock

from tests.framework import (CapturedIOTestCase, SDKTESTER1A_NATIVE1_ID_TOKEN,
                             SDKTESTER1A_ID_ACCESS_TOKEN, get_client_data)
from globus_sdk.auth.token_response import (
    OAuthTokenResponse, OAuthDependentTokenResponse, _convert_token_info_dict)
from globus_sdk.exc import GlobusOptionalDependencyError


class OAuthTokenResponseTests(CapturedIOTestCase):

    def setUp(self):
        """
        Creates a OAuthTokenResponse object with known data for testing
        Sets up mock AuthClient for decoding id_tokens
        """
        super(OAuthTokenResponseTests, self).setUp()
        # known token data for testing expected values
        self.top_token = {  # valid id_token and access_token
            "resource_server": "server1", "expires_in": 10, "scope": "scope1",
            "refresh_token": "RT1", "other_tokens": [], "token_type": "1",
            "id_token": SDKTESTER1A_NATIVE1_ID_TOKEN,
            "access_token": SDKTESTER1A_ID_ACCESS_TOKEN}
        self.other_token1 = {  # invalid id_token with valid access_token
            "resource_server": "server2", "expires_in": 20, "scope": "scope2",
            "refresh_token": "RT2", "other_tokens": [], "token_type": "2",
            "id_token": "invalid_id_token",
            "access_token": SDKTESTER1A_ID_ACCESS_TOKEN}
        self.other_token2 = {  # valid id_token with invalid access_token
            "resource_server": "server3", "expires_in": 30, "scope": "scope3",
            "refresh_token": "RT3", "other_tokens": [], "token_type": "3",
            "id_token": SDKTESTER1A_NATIVE1_ID_TOKEN,
            "access_token": "invalid_access_token"}
        self.top_token["other_tokens"] = [self.other_token1, self.other_token2]

        # create the response
        http_response = requests.Response()
        http_response._content = six.b(json.dumps(self.top_token))
        http_response.headers["Content-Type"] = "application/json"
        self.response = OAuthTokenResponse(http_response)

        # mock AuthClient
        self.ac = mock.Mock()
        self.ac.client_id = get_client_data()["native_app_client1"]["id"]
        self.ac.get = mock.Mock(return_value={
            "jwks_uri":
            u"https://auth.globus.org/jwk.json"})

    def test_convert_token_info_dict(self):
        """
        Converts known info dicts to confirm expected results
        Confirms only refresh_token and token_type may be missing,
        And expires_at is created correctly.
        """
        top_convert = _convert_token_info_dict(self.top_token)

        # expected results for top token data
        for key in ["scope", "access_token", "refresh_token", "token_type"]:
            self.assertEqual(self.top_token[key], top_convert[key])

        # sanity check expires at, assuming test runs within 1 second range
        expected = int(time.time()) + self.top_token["expires_in"]
        self.assertIn(top_convert["expires_at_seconds"],
                      (expected - 1, expected, expected + 1))

        # missing refresh_token or token_type
        for key in ["refresh_token", "token_type"]:
            value = self.top_token.pop(key)
            top_convert = _convert_token_info_dict(self.top_token)
            self.assertIsNone(top_convert[key])
            self.top_token[key] = value

        # required keys
        for key in ["scope", "access_token"]:
            value = self.top_token.pop(key)
            with self.assertRaises(KeyError):
                _convert_token_info_dict(self.top_token)
            self.top_token[key] = value

        # no expires_in makes expires at now, withing a 1 second range
        self.top_token.pop("expires_in")
        top_convert = _convert_token_info_dict(self.top_token)
        expected = int(time.time())
        self.assertIn(top_convert["expires_at_seconds"],
                      (expected - 1, expected, expected + 1))

    def test_by_resource_server(self):
        """
        Gets by_resource_server attribute from test response,
        Confirms expected values found for top and other tokens
        """
        by_server = self.response.by_resource_server

        # confirm data by server matches known token values
        for server, token in [("server1", self.top_token),
                              ("server2", self.other_token1),
                              ("server3", self.other_token2)]:
            server_data = by_server[server]
            for key in ["scope", "access_token",
                        "refresh_token", "token_type"]:
                self.assertEqual(server_data[key], token[key])
            # assumes test runs within 1 second range
            expected = int(time.time()) + token["expires_in"]
            self.assertIn(server_data["expires_at_seconds"],
                          (expected - 1, expected, expected + 1))

    def test_expires_at_seconds(self):
        """
        Gets response's expires_at_seconds attribute, confirms expected value
        """
        # assumes test runs within 1 second range
        expected = int(time.time()) + self.top_token["expires_in"]
        self.assertIn(self.response.expires_at_seconds,
                      (expected - 1, expected, expected + 1))

    def test_expires_in(self):
        """
        Gets two measurements of response's expires_in attribute,
        Sanity checks that expires_in decreases as time goes on
        """
        first_measure = self.response.expires_in
        time.sleep(1.1)
        second_measure = self.response.expires_in
        self.assertTrue(first_measure <= self.top_token["expires_in"])
        self.assertTrue(second_measure < first_measure)

    def test_access_token(self):
        """
        Gets response's access_token attribute, confirms expected value
        """
        self.assertEqual(self.response.access_token,
                         self.top_token["access_token"])

    def test_refresh_token(self):
        """
        Gets response's refresh_token attribute, confirms expected value
        """
        self.assertEqual(self.response.refresh_token,
                         self.top_token["refresh_token"])

    def test_resource_server(self):
        """
        Gets response's resource_server attribute, confirms expected value
        """
        self.assertEqual(self.response.resource_server,
                         self.top_token["resource_server"])

    def test_other_tokens(self):
        """
        Gets response's other_tokens attribute, confirms expected value
        """
        self.assertEqual(self.response.other_tokens,
                         self.top_token["other_tokens"])

    @unittest.skipIf(JOSE_FLAG, "python-jose successfully imported")
    def test_decode_id_token_no_jose(self):
        """
        If jose was not imported, confirms OptionalDependencyError
        """
        with self.assertRaises(GlobusOptionalDependencyError):
            self.response.decode_id_token(self.ac)

    @unittest.skipIf(not JOSE_FLAG, "python-jose not imported")
    def test_decode_id_token_invalid_id(self):
        """
        Creates a response with an invalid id_token, and attempts to decode
        Confirms JWTError
        """
        http_response = requests.Response()
        http_response._content = six.b(json.dumps(self.other_token1))
        http_response.headers["Content-Type"] = "application/json"
        id_response = OAuthTokenResponse(http_response)

        with self.assertRaises(jose.exceptions.JWTError):
            id_response.decode_id_token(self.ac)

    @unittest.skipIf(not JOSE_FLAG, "python-jose not imported")
    def test_decode_id_token_expired(self):
        """
        Attempt to decode an expired id_token, confirms that the token is
        decoded, but errors out on the expired signature.
        """
        with self.assertRaises(jose.exceptions.ExpiredSignatureError):
            self.response.decode_id_token(self.ac)


class OAuthDependentTokenResponseTests(CapturedIOTestCase):

    def setUp(self):
        """
        Creates a OAuthDependentTokenResponse with known data for testing
        """
        super(OAuthDependentTokenResponseTests, self).setUp()
        # known token data for testing expected values
        self.token1 = {
            "resource_server": "server1", "expires_in": 10, "scope": "scope1",
            "access_token": "AT1", "refresh_token": "RT1", "token_type": "1"}
        self.token2 = {
            "resource_server": "server2", "expires_in": 20, "scope": "scope2",
            "access_token": "AT2", "refresh_token": "RT2", "token_type": "2"}
        self.token3 = {
            "resource_server": "server3", "expires_in": 30, "scope": "scope3",
            "access_token": "AT3", "refresh_token": "RT3", "token_type": "3"}

        # create the response
        http_response = requests.Response()
        data = [self.token1, self.token2, self.token3]
        http_response._content = six.b(json.dumps(data))
        http_response.headers["Content-Type"] = "application/json"
        self.response = OAuthDependentTokenResponse(http_response)

    def test_by_resource_server(self):
        """
        Gets by_resource_server attribute from test response,
        Confirms expected values found for top and other tokens
        """
        by_server = self.response.by_resource_server

        # confirm data by server matches known token values
        for server, token in [("server1", self.token1),
                              ("server2", self.token2),
                              ("server3", self.token3)]:
            server_data = by_server[server]
            for key in ["scope", "access_token",
                        "refresh_token", "token_type"]:
                self.assertEqual(server_data[key], token[key])
            # assumes test runs within 1 second range
            expected = int(time.time()) + token["expires_in"]
            self.assertIn(server_data["expires_at_seconds"],
                          (expected - 1, expected, expected + 1))
