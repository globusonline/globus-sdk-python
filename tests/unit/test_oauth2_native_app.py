import hashlib
import base64
from six.moves.urllib.parse import quote
try:
    import mock
except ImportError:
    from unittest import mock

import globus_sdk
from globus_sdk.auth.oauth2_native_app import make_native_app_challenge
from tests.framework import CapturedIOTestCase


class GlobusNativeAppFlowManagerTests(CapturedIOTestCase):

    def setUp(self):
        """
        Inits a GlobusNativeAppFlowManager, uses a mock AuthClient for testing
        """
        super(GlobusNativeAppFlowManagerTests, self).setUp()

        self.ac = mock.Mock()
        self.ac.client_id = "client_id"
        self.ac.base_url = "base_url/"
        self.flow_manager = globus_sdk.auth.GlobusNativeAppFlowManager(
            self.ac, requested_scopes="scopes", redirect_uri="uri",
            state="state", verifier="verifier")

    def test_make_native_app_challenge(self):
        """
        Makes native app challenge with and without verifier,
        Sanity checks results
        """
        # with verifier
        input_verifier = "verifier"
        output_verifier, challenge = make_native_app_challenge(
            input_verifier)

        # sanity check verifier equality and hashing
        self.assertEqual(input_verifier, output_verifier)
        re_hash = hashlib.sha256(input_verifier.encode('utf-8')).digest()
        remade_challenge = base64.urlsafe_b64encode(re_hash).decode('utf-8')
        self.assertEqual(challenge, remade_challenge)

        # without verifier
        verifier, challenge = make_native_app_challenge()

        # sanity check verifier format and hashing
        self.assertEqual(len(verifier), 36)
        for i in [8, 13, 18, 23]:
            self.assertEqual(verifier[i], "-")
        re_hash = hashlib.sha256(verifier.encode('utf-8')).digest()
        remade_challenge = base64.urlsafe_b64encode(re_hash).decode('utf-8')
        self.assertEqual(challenge, remade_challenge)

    def test_get_authorize_url(self):
        """
        Creates an authorize url, confirms results match object values
        Confirms additional params passed appear in the url
        """
        url = self.flow_manager.get_authorize_url()

        expected_vals = [self.ac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + self.ac.client_id,
                         "redirect_uri=" + self.flow_manager.redirect_uri,
                         "scope=" + self.flow_manager.requested_scopes,
                         "state=" + self.flow_manager.state,
                         "response_type=code",
                         "code_challenge=" +
                         quote(self.flow_manager.challenge),
                         "code_challenge_method=S256",
                         "access_type=online",
                         ]
        for val in expected_vals:
            self.assertIn(val, url)

        # confirm additional params are passed
        params = {"param1": "value1", "param2": "value2"}
        param_url = self.flow_manager.get_authorize_url(
            additional_params=params)
        for param, value in params.items():
            self.assertIn(param + "=" + value, param_url)

    def test_prefill_named_grant(self):
        """
        Should add the `prefill_named_grant` query string parameter
        to the authorize url.
        """
        flow_with_prefill = globus_sdk.auth.GlobusNativeAppFlowManager(
            self.ac, requested_scopes="scopes", redirect_uri="uri",
            state="state", verifier="verifier", prefill_named_grant="test")

        authorize_url = flow_with_prefill.get_authorize_url()

        self.assertIn('prefill_named_grant=test', authorize_url)

        flow_without_prefill = globus_sdk.auth.GlobusNativeAppFlowManager(
            self.ac, requested_scopes="scopes", redirect_uri="uri",
            state="state", verifier="verifier")

        authorize_url = flow_without_prefill.get_authorize_url()

        self.assertNotIn('prefill_named_grant=', authorize_url)

    def test_exchange_code_for_tokens(self):
        """
        Makes a token exchange with the mock AuthClient,
        Confirms AuthClient gets and sends correct data.
        """
        auth_code = "code"
        self.flow_manager.exchange_code_for_tokens(auth_code)

        expected = {"client_id": self.ac.client_id,
                    "grant_type": "authorization_code",
                    "code": auth_code.encode("utf-8"),
                    "code_verifier": self.flow_manager.verifier,
                    "redirect_uri": self.flow_manager.redirect_uri}
        self.ac.oauth2_token.assert_called_with(expected)
