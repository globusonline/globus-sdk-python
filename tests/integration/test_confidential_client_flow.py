from six.moves.urllib.parse import quote_plus

import globus_sdk
from globus_sdk.auth.oauth2_constants import DEFAULT_REQUESTED_SCOPES
from tests.framework import CapturedIOTestCase, get_client_data
from globus_sdk.auth import GlobusAuthorizationCodeFlowManager
from globus_sdk.exc import GlobusAPIError


class ConfidentialAppAuthClientIntegrationTests(CapturedIOTestCase):

    def setUp(self):
        """
        Creates a ConfidentialAppAuthClient for testing
        """
        super(ConfidentialAppAuthClientIntegrationTests, self).setUp()
        client_data = get_client_data()["confidential_app_client1"]
        self.cac = globus_sdk.ConfidentialAppAuthClient(
            client_id=client_data["id"],
            client_secret=client_data["secret"])

    def test_oauth2_start_flow_default(self):
        """
        Starts a default GlobusAuthorizationCodeFlowManager,
        Confirms flow is initialized as expected, and can be used.
        """
        # starting with no flow
        self.assertIsNone(self.cac.current_oauth2_flow_manager)

        # confirms flow initialized with default flow values
        flow = self.cac.oauth2_start_flow("uri")
        self.assertIsInstance(flow, GlobusAuthorizationCodeFlowManager)
        self.assertEqual(flow.redirect_uri, "uri")
        self.assertEqual(flow.requested_scopes, DEFAULT_REQUESTED_SCOPES)
        self.assertEqual(flow.state, "_default")
        self.assertFalse(flow.refresh_tokens)

        # confirm client can get url via flow
        url_res = self.cac.oauth2_get_authorize_url()
        expected_vals = [self.cac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + self.cac.client_id,
                         "redirect_uri=" + "uri",
                         "scope=" + quote_plus(DEFAULT_REQUESTED_SCOPES),
                         "state=" + "_default",
                         "access_type=" + "online"]
        for val in expected_vals:
            self.assertIn(val, url_res)

        # confirm client can try exchanging code for tokens via flow
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.cac.oauth2_exchange_code_for_tokens("invalid_code")
        self.assertEqual(apiErr.exception.http_status, 401)
        self.assertEqual(apiErr.exception.code, "Error")

    def test_oauth2_start_flow_specified(self):
        """
        Starts a GlobusAuthorizationCodeFlowManager with specified parameters,
        Confirms flow is initialized as expected, and can be used.
        """
        # starting with no flow
        self.assertIsNone(self.cac.current_oauth2_flow_manager)

        # confirms flow initialized with specified values
        flow = self.cac.oauth2_start_flow("uri", requested_scopes="scopes",
                                          state="state", refresh_tokens=True)
        self.assertIsInstance(flow, GlobusAuthorizationCodeFlowManager)
        self.assertEqual(flow.redirect_uri, "uri")
        self.assertEqual(flow.requested_scopes, "scopes")
        self.assertEqual(flow.state, "state")
        self.assertTrue(flow.refresh_tokens)

        # confirm client can get url via flow
        url_res = self.cac.oauth2_get_authorize_url()
        expected_vals = [self.cac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + self.cac.client_id,
                         "redirect_uri=" + "uri",
                         "scope=" + "scope",
                         "state=" + "state",
                         "access_type=" + "offline"]
        for val in expected_vals:
            self.assertIn(val, url_res)

        # confirm client can try exchanging code for tokens via flow
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.cac.oauth2_exchange_code_for_tokens("invalid_code")
        self.assertEqual(apiErr.exception.http_status, 401)
        self.assertEqual(apiErr.exception.code, "Error")
