import time
try:
    import mock
except ImportError:
    from unittest import mock

from globus_sdk.authorizers import RefreshTokenAuthorizer
from globus_sdk.authorizers.refresh_token import EXPIRES_ADJUST_SECONDS
from tests.framework import CapturedIOTestCase


class RefreshTokenAuthorizerTests(CapturedIOTestCase):

    def setUp(self):
        """
        Sets up a RefreshTokenAuthorizer using a mock AuthClient for testing
        """
        super(RefreshTokenAuthorizerTests, self).setUp()
        # init values for testing
        self.refresh_token = "refresth_token_1"
        self.access_token = "access_token_1"
        # set to expires 1 second in the future (after buffer time)
        self.expires_at = int(time.time()) + EXPIRES_ADJUST_SECONDS + 1
        self.on_refresh = mock.Mock()

        # mock response value for simulating a refresh token grant response
        self.response = mock.Mock()
        self.response.expires_at_seconds = int(time.time()) + 1000
        self.response.access_token = "access_token_2"

        # mock AuthClient for testing
        self.ac = mock.Mock()
        self.ac.oauth2_refresh_token = mock.Mock(return_value=self.response)

        self.authorizer = RefreshTokenAuthorizer(
            self.refresh_token, self.ac, access_token=self.access_token,
            expires_at=self.expires_at, on_refresh=self.on_refresh)

    def test_init(self):
        """
        Inits a RefreshTokenAuthorizer with an access_token, but no expires_at,
        and a RefreshTokenAuthorizer with an expires_at, but no access_token.
        Confirms that a new access_token is gotten for safety
        """
        authorizer = RefreshTokenAuthorizer(
            self.refresh_token, self.ac, access_token=self.access_token)
        self.assertEqual(authorizer.access_token, self.response.access_token)

        authorizer = RefreshTokenAuthorizer(
            self.refresh_token, self.ac, expires_at=self.access_token)
        self.assertEqual(authorizer.access_token, self.response.access_token)

    def test_set_expiration_time(self):
        """
        Confirms expiration time is set earlier than input value for a buffer
        """
        # confirm initial value was adjusted automatically
        self.assertEqual(self.authorizer.expires_at,
                         self.expires_at - EXPIRES_ADJUST_SECONDS)

        # confirm results with test inputs
        for test_input in [0, 60, 120, 1200]:
            self.authorizer._set_expiration_time(test_input)
            self.assertEqual(self.authorizer.expires_at,
                             test_input - EXPIRES_ADJUST_SECONDS)

    def test_get_new_access_token(self):
        """
        Calls get_new_acces token, confirms that the mock AuthClient is used
        and that the mock on_refresh function is called.
        """
        # confirm starting with original access_token
        self.assertEqual(self.authorizer.access_token, self.access_token)

        # get new_access_token
        self.authorizer._get_new_access_token()
        # confirm side effects
        self.assertEqual(self.authorizer.access_token,
                         self.response.access_token)
        self.assertEqual(self.authorizer.expires_at,
                         self.response.expires_at_seconds -
                         EXPIRES_ADJUST_SECONDS)
        self.ac.oauth2_refresh_token.assert_called_once_with(
            self.refresh_token)
        self.on_refresh.assert_called_once()

    def test_check_expiration_time_valid(self):
        """
        Confirms nothing is done before the access_token expires,
        """
        self.authorizer._check_expiration_time()
        self.assertEqual(self.authorizer.access_token, self.access_token)

    def test_check_expiration_time_expired(self):
        """
        Confirms a new access_token is gotten after waiting for expiration
        """
        time.sleep(1)
        self.authorizer._check_expiration_time()
        self.assertEqual(self.authorizer.access_token,
                         self.response.access_token)
        self.assertEqual(self.authorizer.expires_at,
                         self.response.expires_at_seconds -
                         EXPIRES_ADJUST_SECONDS)

    def test_check_expiration_time_no_token(self):
        """
        Confirms a new access_token is gotten if the old one is set to None
        """
        self.authorizer.access_token = None
        self.authorizer._check_expiration_time()
        self.assertEqual(self.authorizer.access_token,
                         self.response.access_token)
        self.assertEqual(self.authorizer.expires_at,
                         self.response.expires_at_seconds -
                         EXPIRES_ADJUST_SECONDS)

    def test_check_expiration_time_no_expiration(self):
        """
        Confirms a new access_token is gotten if expires_at is set to None
        """
        self.authorizer.expires_at = None
        self.authorizer._check_expiration_time()
        self.assertEqual(self.authorizer.access_token,
                         self.response.access_token)
        self.assertEqual(self.authorizer.expires_at,
                         self.response.expires_at_seconds -
                         EXPIRES_ADJUST_SECONDS)

    def test_set_authorization_header(self):
        """
        Sets authorization header on a test dictionary, confirms expected value
        """
        header_dict = {}
        self.authorizer.set_authorization_header(header_dict)
        # confirm value
        self.assertEqual(header_dict["Authorization"],
                         "Bearer " + self.access_token)

    def test_set_authorization_header_existing(self):
        """
        Confirms that an existing Authorization field is overwritten
        """
        header_dict = {"Header": "value",
                       "Authorization": "previous_value"}
        self.authorizer.set_authorization_header(header_dict)
        # confirm values
        self.assertEqual(header_dict["Authorization"],
                         "Bearer " + self.access_token)
        self.assertEqual(header_dict["Header"], "value")

    def test_set_authorization_header_expired(self):
        """
        Waits for the access_token to expire, then sets authorization header
        Confirms header value uses the new access_token.
        """
        header_dict = {}
        time.sleep(1)

        self.authorizer.set_authorization_header(header_dict)
        # confirm value
        self.assertEqual(header_dict["Authorization"],
                         "Bearer " + self.response.access_token)

    def test_set_authorization_header_no_token(self):
        """
        Sets the access_token to None, then sets authorization header
        Confirms header value uses the new access_token.
        """
        header_dict = {}
        self.authorizer.access_token = None

        self.authorizer.set_authorization_header(header_dict)
        # confirm value
        self.assertEqual(header_dict["Authorization"],
                         "Bearer " + self.response.access_token)

    def test_set_authorization_header_no_expires(self):
        """
        Sets expires_at to None, then sets authorization header
        Confirms header value uses the new access_token.
        """
        header_dict = {}
        self.authorizer.expires_at = None

        self.authorizer.set_authorization_header(header_dict)
        # confirm value
        self.assertEqual(header_dict["Authorization"],
                         "Bearer " + self.response.access_token)

    def test_handle_missing_authorization(self):
        """
        Confirms that RefreshTokenAuthorizers will attempt to fix 401s
        by treating their existing access_token as expired
        """
        self.assertTrue(self.authorizer.handle_missing_authorization())
        self.assertIsNone(self.authorizer.expires_at)
