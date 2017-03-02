from globus_sdk.authorizers import AccessTokenAuthorizer
from tests.framework import CapturedIOTestCase


class AccessTokenAuthorizerTests(CapturedIOTestCase):

    def setUp(self):
        """
        Initializes a AccessTokenAuthorizer for testing
        """
        super(AccessTokenAuthorizerTests, self).setUp()
        self.token = "token"
        self.authorizer = AccessTokenAuthorizer(self.token)

    def test_set_authorization_header(self):
        """
        Sets authorization header in a test dictionary, confirms expected value
        """
        header_dict = {}
        self.authorizer.set_authorization_header(header_dict)
        # confirm value
        self.assertEqual(header_dict["Authorization"], "Bearer " + self.token)

    def test_set_authorization_header_existing(self):
        """
        Confirms that an existing Authorization field is overwritten
        """
        header_dict = {"Header": "value",
                       "Authorization": "previous_value"}
        self.authorizer.set_authorization_header(header_dict)
        # confirm values
        self.assertEqual(header_dict["Authorization"], "Bearer " + self.token)
        self.assertEqual(header_dict["Header"], "value")

    def test_handle_missing_authorization(self):
        """
        Confirms that AccessTokenAuthorizer doesnt handle missing authorization
        """
        self.assertFalse(self.authorizer.handle_missing_authorization())
