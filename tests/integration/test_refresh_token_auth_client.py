try:
    import mock
except ImportError:
    from unittest import mock

import globus_sdk
from tests.framework import (CapturedIOTestCase,
                             get_client_data, GO_EP1_ID,
                             SDKTESTER1A_NATIVE1_TRANSFER_RT)
from globus_sdk.exc import GlobusAPIError


class RefreshTokenAuthorizerIntegrationTests(CapturedIOTestCase):

    def setUp(self):
        """
        Makes a refresh_token grant to get new tokens for teseting
        Sets up an AuthClient and a RefreshTokenAuthorizer with a mock
        on_refresh function for testing their interactions
        """
        super(RefreshTokenAuthorizerIntegrationTests, self).setUp()

        client_id = get_client_data()["native_app_client1"]["id"]
        form_data = {'refresh_token': SDKTESTER1A_NATIVE1_TRANSFER_RT,
                     'grant_type': 'refresh_token',
                     'client_id': client_id}
        token_res = globus_sdk.AuthClient().oauth2_token(form_data)

        self.access_token = token_res.access_token
        self.expires_at = token_res.expires_at_seconds

        self.on_refresh = mock.Mock()
        self.nac = globus_sdk.NativeAppAuthClient(
            client_id=get_client_data()["native_app_client1"]["id"])
        self.authorizer = globus_sdk.RefreshTokenAuthorizer(
            SDKTESTER1A_NATIVE1_TRANSFER_RT, self.nac,
            access_token=self.access_token, expires_at=self.expires_at,
            on_refresh=self.on_refresh)
        self.tc = globus_sdk.TransferClient(authorizer=self.authorizer)

    def test_get_new_access_token(self):
        """
        Has the Authorizer get a new access_token via the AuthClient
        Confirms on_refresh is called, and a different, valid token exists
        """
        # get new access token and confirm side effects
        self.authorizer._get_new_access_token()
        self.on_refresh.assert_called_once()
        self.assertNotEqual(self.access_token, self.authorizer.access_token)

        # confirm AuthClient is still usable with new token
        get_res = self.tc.get_endpoint(GO_EP1_ID)
        self.assertEqual(get_res["id"], GO_EP1_ID)

    def test_invalid_access_token(self):
        """
        Invalidates the Authorizer's access_token, then makes a request
        Confirms new access_token is is gotten and request is successful.
        """
        self.nac.oauth2_revoke_token(self.access_token)

        # make request, confirm successful despite invalid access_token
        get_res = self.tc.get_endpoint(GO_EP1_ID)
        self.assertEqual(get_res["id"], GO_EP1_ID)
        # confirm new token was gotten
        self.on_refresh.assert_called_once()
        self.assertNotEqual(self.access_token, self.authorizer.access_token)

    def test_invalid_access_token_no_retry(self):
        """
        Invalidates the Authorizer's access_token, then makes a request
        with retry_401=False, confirms 401
        """
        self.nac.oauth2_revoke_token(self.access_token)

        # make request, confirm 401
        with self.assertRaises(GlobusAPIError) as apiErr:
            path = self.tc.qjoin_path("endpoint", GO_EP1_ID)
            self.tc.get(path, retry_401=False)
        self.assertEqual(apiErr.exception.http_status, 401)
        self.assertEqual(apiErr.exception.code, "AuthenticationFailed")

    def test_invalid_tokens(self):
        """
        Invalidates the Authorizer's refresh_token and access_tokens,
        confirms irrecoverable
        """
        # TODO: Get a new refresh_token to revoke here instead
        self.authorizer.refresh_token = None
        self.nac.oauth2_revoke_token(self.access_token)

        # confirm irrecoverable
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.tc.get_endpoint(GO_EP1_ID)
        self.assertEqual(apiErr.exception.http_status, 400)
        self.assertEqual(apiErr.exception.code, "Error")
