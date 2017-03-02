from six.moves.urllib.parse import quote_plus

import globus_sdk
from globus_sdk.auth.oauth2_constants import DEFAULT_REQUESTED_SCOPES
from globus_sdk.auth.oauth2_native_app import make_native_app_challenge
from tests.framework import CapturedIOTestCase, get_client_data
from globus_sdk.auth import GlobusNativeAppFlowManager
from globus_sdk.exc import GlobusAPIError


class NativeAppAuthClientIntegrationTests(CapturedIOTestCase):

    def setUp(self):
        """
        Creates a NativeAppAuthClient for testing
        """
        super(NativeAppAuthClientIntegrationTests, self).setUp()
        self.nac = globus_sdk.NativeAppAuthClient(
            client_id=get_client_data()["native_app_client1"]["id"])

    def test_oauth2_start_flow_default(self):
        """
        Starts a default GlobusNativeAppFlowManager,
        Confirms flow is initialized as expected, and can be used.
        """
        # starting with no flow
        self.assertIsNone(self.nac.current_oauth2_flow_manager)

        # confirms flow initialized with default flow values
        flow = self.nac.oauth2_start_flow()
        self.assertIsInstance(flow, GlobusNativeAppFlowManager)
        self.assertEqual(flow.redirect_uri,
                         self.nac.base_url + "v2/web/auth-code")
        self.assertEqual(flow.requested_scopes, DEFAULT_REQUESTED_SCOPES)
        self.assertEqual(flow.state, "_default")
        self.assertFalse(flow.refresh_tokens)

        # confirm client can get url via flow
        url_res = self.nac.oauth2_get_authorize_url()
        expected_vals = [self.nac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + self.nac.client_id,
                         "redirect_uri=" +
                         quote_plus(self.nac.base_url + "v2/web/auth-code"),
                         "scope=" + quote_plus(DEFAULT_REQUESTED_SCOPES),
                         "state=" + "_default",
                         "code_challenge=" + quote_plus(flow.challenge),
                         "access_type=" + "online"]
        for val in expected_vals:
            self.assertIn(val, url_res)

        # confirm client can try exchanging code for tokens via flow
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.nac.oauth2_exchange_code_for_tokens("invalid_code")
        self.assertEqual(apiErr.exception.http_status, 401)
        self.assertEqual(apiErr.exception.code, "Error")

    def test_oauth2_start_flow_specified(self):
        """
        Starts a GlobusNativeAppFlowManager with specified parameters,
        Confirms flow is initialized as expected, and can be used.
        """
        # starting with no flow
        self.assertIsNone(self.nac.current_oauth2_flow_manager)

        # confirms flow initialized with specified values
        flow = self.nac.oauth2_start_flow(
            requested_scopes="scopes", redirect_uri="uri",
            state="state", verifier="verifier", refresh_tokens=True)
        self.assertIsInstance(flow, GlobusNativeAppFlowManager)
        self.assertEqual(flow.redirect_uri, "uri")
        self.assertEqual(flow.requested_scopes, "scopes")
        self.assertEqual(flow.state, "state")
        self.assertTrue(flow.refresh_tokens)

        # confirm client can get url via flow
        url_res = self.nac.oauth2_get_authorize_url()
        verifier, remade_challenge = make_native_app_challenge("verifier")
        expected_vals = [self.nac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + self.nac.client_id,
                         "redirect_uri=" + "uri",
                         "scope=" + "scopes",
                         "state=" + "state",
                         "code_challenge=" + quote_plus(remade_challenge),
                         "access_type=" + "offline"]
        for val in expected_vals:
            self.assertIn(val, url_res)

        # confirm client can try exchanging code for tokens via flow
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.nac.oauth2_exchange_code_for_tokens("invalid_code")
        self.assertEqual(apiErr.exception.http_status, 401)
        self.assertEqual(apiErr.exception.code, "Error")
