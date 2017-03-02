from six.moves.urllib.parse import quote_plus

import globus_sdk
from globus_sdk.auth.oauth2_constants import DEFAULT_REQUESTED_SCOPES
from globus_sdk.auth.oauth2_native_app import make_native_app_challenge
from tests.framework import CapturedIOTestCase, get_client_data
from globus_sdk.exc import GlobusAPIError


class AuthClientIntegrationTests(CapturedIOTestCase):

    def test_oauth2_get_authorize_url_native(self):
        """
        Starts an auth flow with a NativeAppFlowManager, gets the authorize url
        validates expected results with both default and specified parameters.
        """
        ac = globus_sdk.AuthClient(
            client_id=get_client_data()["native_app_client1"]["id"])

        # default parameters for starting auth flow
        flow_manager = globus_sdk.auth.GlobusNativeAppFlowManager(ac)
        ac.current_oauth2_flow_manager = flow_manager

        # get url_and validate results
        url_res = ac.oauth2_get_authorize_url()
        expected_vals = [ac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + ac.client_id,
                         "redirect_uri=" +
                         quote_plus(ac.base_url + "v2/web/auth-code"),
                         "scope=" + quote_plus(DEFAULT_REQUESTED_SCOPES),
                         "state=" + "_default",
                         "response_type=" + "code",
                         "code_challenge=" +
                         quote_plus(flow_manager.challenge),
                         "code_challenge_method=" + "S256",
                         "access_type=" + "online"]
        for val in expected_vals:
            self.assertIn(val, url_res)

        # starting flow with specified paramaters
        flow_manager = globus_sdk.auth.GlobusNativeAppFlowManager(
            ac, requested_scopes="scopes", redirect_uri="uri",
            state="state", verifier="verifier", refresh_tokens=True)
        ac.current_oauth2_flow_manager = flow_manager

        # get url_and validate results
        url_res = ac.oauth2_get_authorize_url()
        verifier, remade_challenge = make_native_app_challenge("verifier")
        expected_vals = [ac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + ac.client_id,
                         "redirect_uri=" + "uri",
                         "scope=" + "scopes",
                         "state=" + "state",
                         "response_type=" + "code",
                         "code_challenge=" + quote_plus(remade_challenge),
                         "code_challenge_method=" + "S256",
                         "access_type=" + "offline"]
        for val in expected_vals:
            self.assertIn(val, url_res)

    def test_oauth2_get_authorize_url_confidential(self):
        """
        Starts an auth flow with a NativeAppFlowManager, gets the authorize url
        validates expected results with both default and specified parameters.
        """
        ac = globus_sdk.AuthClient(
            client_id=get_client_data()["confidential_app_client1"]["id"])

        # default parameters for starting auth flow
        flow_manager = globus_sdk.auth.GlobusAuthorizationCodeFlowManager(
            ac, "uri")
        ac.current_oauth2_flow_manager = flow_manager

        # get url_and validate results
        url_res = ac.oauth2_get_authorize_url()
        expected_vals = [ac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + ac.client_id,
                         "redirect_uri=" + "uri",
                         "scope=" + quote_plus(DEFAULT_REQUESTED_SCOPES),
                         "state=" + "_default",
                         "response_type=" + "code",
                         "access_type=" + "online"]
        for val in expected_vals:
            self.assertIn(val, url_res)

        # starting flow with specified paramaters
        flow_manager = globus_sdk.auth.GlobusAuthorizationCodeFlowManager(
            ac, requested_scopes="scopes", redirect_uri="uri",
            state="state", refresh_tokens=True)
        ac.current_oauth2_flow_manager = flow_manager

        # get url_and validate results
        url_res = ac.oauth2_get_authorize_url()
        expected_vals = [ac.base_url + "v2/oauth2/authorize?",
                         "client_id=" + ac.client_id,
                         "redirect_uri=" + "uri",
                         "scope=" + "scopes",
                         "state=" + "state",
                         "response_type=" + "code",
                         "access_type=" + "offline"]
        for val in expected_vals:
            self.assertIn(val, url_res)

    def test_oauth2_exchange_code_for_tokens_native(self):
        """
        Starts a NativeAppFlowManager, Confirms invalid code raises 401
        Further testing cannot be done without user login credentials
        """
        ac = globus_sdk.AuthClient(
            client_id=get_client_data()["native_app_client1"]["id"])
        flow_manager = globus_sdk.auth.GlobusNativeAppFlowManager(ac)
        ac.current_oauth2_flow_manager = flow_manager

        with self.assertRaises(GlobusAPIError) as apiErr:
            ac.oauth2_exchange_code_for_tokens("invalid_code")
        self.assertEqual(apiErr.exception.http_status, 401)
        self.assertEqual(apiErr.exception.code, "Error")

    def test_oauth2_exchange_code_for_tokens_confidential(self):
        """
        Starts an AuthorizationCodeFlowManager, Confirms bad code raises 401
        Further testing cannot be done without user login credentials
        """
        ac = globus_sdk.AuthClient(
            client_id=get_client_data()["confidential_app_client1"]["id"])
        flow_manager = globus_sdk.auth.GlobusAuthorizationCodeFlowManager(
            ac, "uri")
        ac.current_oauth2_flow_manager = flow_manager

        with self.assertRaises(GlobusAPIError) as apiErr:
            ac.oauth2_exchange_code_for_tokens("invalid_code")
        self.assertEqual(apiErr.exception.http_status, 401)
        self.assertEqual(apiErr.exception.code, "Error")
