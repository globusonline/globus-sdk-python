from globus_sdk.authorizers import NullAuthorizer
from tests.framework import CapturedIOTestCase


class NullAuthorizerTests(CapturedIOTestCase):

    def setUp(self):
        """
        Initializes a NullAuthorizer for testing
        """
        super(NullAuthorizerTests, self).setUp()
        self.authorizer = NullAuthorizer()

    def test_set_authorization_header(self):
        """
        Sets authorization header in a test dictionary,
        Confirms that nothing happens.
        and any existing Authorization header is removed
        """
        header_dict = {}
        self.authorizer.set_authorization_header(header_dict)
        self.assertEqual(header_dict, {})

    def test_set_authorization_header_existing(self):
        """
        Confirms that an existing Authorization field is removed
        """
        header_dict = {"Header": "value",
                       "Authorization": "previous_value"}
        self.authorizer.set_authorization_header(header_dict)
        self.assertEqual(header_dict, {"Header": "value"})

    def test_handle_missing_authorization(self):
        """
        Confirms that NullAuthorizer doesn't handle missing authorization
        """
        self.assertFalse(self.authorizer.handle_missing_authorization())
