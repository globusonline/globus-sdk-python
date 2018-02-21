import six
import logging
from random import getrandbits

import globus_sdk
from globus_sdk.base import (BaseClient, safe_stringify,
                             slash_join, merge_params)
from tests.framework import (CapturedIOTestCase, get_client_data,
                             SDKTESTER1A_NATIVE1_TRANSFER_RT, retry_errors)
from globus_sdk.exc import GlobusAPIError


class BaseClientTests(CapturedIOTestCase):

    @classmethod
    def setUpClass(self):
        """
        Creates a BaseClient object for testing
        """
        ac = globus_sdk.NativeAppAuthClient(
            client_id=get_client_data()["native_app_client1"]["id"])
        authorizer = globus_sdk.RefreshTokenAuthorizer(
            SDKTESTER1A_NATIVE1_TRANSFER_RT, ac)
        self.bc = BaseClient("transfer", base_path="/v0.10/",
                             authorizer=authorizer)

    def setUp(self):
        """
        Creates a list for tracking cleanup of assets created during testing
        Sets up a test endpoint
        """
        super(BaseClientTests, self).setUp()

        # list of dicts, each containing a function and a list of args
        # to pass to that function s.t. calling f(*args) cleans an asset
        self.asset_cleanup = []

        # set up test endpoint
        # name randomized to prevent collision
        data = {"display_name": "Base Test Endpoint-" + str(getrandbits(128))}
        r = self.bc.post("endpoint", data)
        self.test_ep_id = safe_stringify(r["id"])
        # track asset for cleanup
        path = self.bc.qjoin_path("endpoint", self.test_ep_id)
        self.asset_cleanup.append({"function": self.bc.delete,
                                   "args": [path],
                                   "name": "test_ep"})  # for ease of removal

    def tearDown(self):
        """
        Parses asset_cleanup to destroy all assets created during testing
        """
        super(BaseClientTests, self).tearDown()
        # call the cleanup functions with the arguments they were given
        for cleanup in self.asset_cleanup:
            cleanup["function"](*cleanup["args"])

    def test_client_log_adapter(self):
        """
        Logs a test message with the base client's logger,
        Confirms the ClientLogAdapter marks the message with the client
        """
        # make a MemoryHandler for capturing the log in a buffer)
        memory_handler = logging.handlers.MemoryHandler(1028)
        self.bc.logger.logger.addHandler(memory_handler)
        # send the test message
        in_msg = "Testing ClientLogAdapter"
        self.bc.logger.info(in_msg)
        # confirm results
        out_msg = memory_handler.buffer[0].getMessage()
        expected_msg = "[instance:{0}] {1}".format(id(self.bc), in_msg)
        self.assertEqual(expected_msg, out_msg)

        memory_handler.close()
        self.bc.logger.logger.removeHandler(memory_handler)

    def test_set_app_name(self):
        """
        Sets app name, confirms results
        """
        # set app name
        app_name = "SDK Test"
        self.bc.set_app_name(app_name)
        # confirm results
        self.assertEqual(self.bc.app_name, app_name)
        self.assertEqual(self.bc._headers['User-Agent'],
                         '{0}/{1}'.format(self.bc.BASE_USER_AGENT, app_name))

    def test_qjoin_path(self):
        """
        Calls qjoin on parts to form a path, confirms results
        """
        parts = ["SDK", "Test", "Path", "Items"]
        path = self.bc.qjoin_path(*parts)
        self.assertEqual(path, "/SDK/Test/Path/Items")

    @retry_errors()
    def test_get(self):
        """
        Gets test endpoint, verifies results
        Sends nonsense get, confirms 404
        Sends get to non-get resource, confirms 405
        """
        # get test endpoint
        path = self.bc.qjoin_path("endpoint", self.test_ep_id)
        get_res = self.bc.get(path)
        # validate results
        self.assertIn("display_name", get_res)
        self.assertIn("canonical_name", get_res)
        self.assertEqual(get_res["DATA_TYPE"], "endpoint")
        self.assertEqual(get_res["id"], self.test_ep_id)

        # send nonsense get
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.get("nonsense_path")
        self.assertEqual(apiErr.exception.http_status, 404)
        self.assertEqual(apiErr.exception.code, "ClientError.NotFound")

        # send get to endpoint without id (post resource)
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.get("endpoint")
        self.assertEqual(apiErr.exception.http_status, 405)
        self.assertEqual(apiErr.exception.code, "ClientError.BadMethod")

    @retry_errors()
    def test_post(self):
        """
        Makes a test endpoint, verifies results
        Sends nonsense post, confirms 404
        Sends post without data, confirms 400
        Sends post to non-post resource, confirms 405
        """
        # post to create a new endpoint, name randomized to prevent collision
        post_data = {"display_name": "Post Test-" + str(getrandbits(128))}
        post_res = self.bc.post("endpoint", post_data)
        # validate results
        self.assertIn("id", post_res)
        self.assertEqual(post_res["DATA_TYPE"], "endpoint_create_result")
        self.assertEqual(post_res["code"], "Created")
        self.assertEqual(post_res["message"], "Endpoint created successfully")
        # track asset for cleanup
        path = self.bc.qjoin_path("endpoint", safe_stringify(post_res["id"]))
        self.asset_cleanup.append({"function": self.bc.delete, "args": [path]})

        # send nonsense post
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.post("nonsense_path")
        self.assertEqual(apiErr.exception.http_status, 404)
        self.assertEqual(apiErr.exception.code, "ClientError.NotFound")

        # send post without data
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.post("endpoint")
        self.assertEqual(apiErr.exception.http_status, 400)
        self.assertEqual(apiErr.exception.code, "BadRequest")

        # send post to endpoint with id (get/delete resource)
        with self.assertRaises(GlobusAPIError) as apiErr:
            path = self.bc.qjoin_path("endpoint", self.test_ep_id)
            self.bc.post(path)
        self.assertEqual(apiErr.exception.http_status, 405)
        self.assertEqual(apiErr.exception.code, "ClientError.BadMethod")

    @retry_errors()
    def test_delete(self):
        """
        Deletes the test endpoint, verifies results
        Confirms trying to delete non existent items raises 404
        Sends nonsense delete, confirms 404
        Sends delete to non-delete resource, confirms 405
        """
        # delete the test endpoint
        path = self.bc.qjoin_path("endpoint", self.test_ep_id)
        del_res = self.bc.delete(path)
        # validate results
        self.assertEqual(del_res["DATA_TYPE"], "result")
        self.assertEqual(del_res["code"], "Deleted")
        self.assertEqual(del_res["message"],
                         "Endpoint deleted successfully")
        # stop tracking asset for cleanup
        for cleanup in self.asset_cleanup:
            if "name" in cleanup and cleanup["name"] == "test_ep":
                self.asset_cleanup.remove(cleanup)
                break

        # attempt to delete the test endpoint again
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.delete(path)
        self.assertEqual(apiErr.exception.http_status, 404)
        self.assertEqual(apiErr.exception.code, "EndpointNotFound")

        # send nonsense delete
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.delete("nonsense_path")
        self.assertEqual(apiErr.exception.http_status, 404)
        self.assertEqual(apiErr.exception.code, "ClientError.NotFound")

        # send delete to endpoint w/o id (post resource)
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.delete("endpoint")
        self.assertEqual(apiErr.exception.http_status, 405)
        self.assertEqual(apiErr.exception.code, "ClientError.BadMethod")

    @retry_errors()
    def test_put(self):
        """
        Updates test endpoint, verifies results
        Sends nonsense put, confirms 404
        Sends put without data, confirms 400
        Sends put to non-put resource, confirms 405
        """
        # update test endpoint with put, name randomized to prevent collision
        put_data = {"display_name": "Put Test-" + str(getrandbits(128))}
        path = self.bc.qjoin_path("endpoint", self.test_ep_id)
        put_res = self.bc.put(path, put_data)
        # validate results
        self.assertEqual(put_res["DATA_TYPE"], "result")
        self.assertEqual(put_res["code"], "Updated")
        self.assertEqual(put_res["message"], "Endpoint updated successfully")

        # send nonsense put
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.put("nonsense_path")
        self.assertEqual(apiErr.exception.http_status, 404)
        self.assertEqual(apiErr.exception.code, "ClientError.NotFound")

        # send put without data
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.put(path)
        self.assertEqual(apiErr.exception.http_status, 400)
        self.assertEqual(apiErr.exception.code, "BadRequest")

        # send put to endpoint w/o id (post resource)
        with self.assertRaises(GlobusAPIError) as apiErr:
            self.bc.put("endpoint")
        self.assertEqual(apiErr.exception.http_status, 405)
        self.assertEqual(apiErr.exception.code, "ClientError.BadMethod")

    def test_slash_join(self):
        """
        slash_joins a's with and without trailing "/"
        to b's with and without leading "/"
        Confirms all have the same correct slash_join output
        """
        for a in ["a", "a/"]:
            for b in ["b", "/b"]:
                self.assertEqual(slash_join(a, b), "a/b")

    def test_merge_params(self):
        """
        Merges a base parameter dict with other paramaters, validates results
        Confirms works with explicit dictionaries and arguments
        Confirms new parameters set to None are ignored
        Confirms new parameters overwrite old ones (is this correct?)
        """

        # explicit dictionary merging
        params = {"param1": "value1"}
        extra = {"param2": "value2", "param3": "value3"}
        merge_params(params, **extra)
        expected = {"param1": "value1", "param2": "value2", "param3": "value3"}
        self.assertEqual(params, expected)

        # arguments
        params = {"param1": "value1"}
        merge_params(params, param2="value2", param3="value3")
        expected = {"param1": "value1", "param2": "value2", "param3": "value3"}
        self.assertEqual(params, expected)

        # ignoring parameters set to none
        params = {"param1": "value1"}
        merge_params(params, param2=None, param3=None)
        expected = {"param1": "value1"}
        self.assertEqual(params, expected)

        # existing parameters
        params = {"param": "value"}
        merge_params(params, param="newValue")
        expected = {"param": "newValue"}
        self.assertEqual(params, expected)

    def test_safe_stringify(self):
        """
        safe_stringifies strings, bytes, explicit unicode, an int, an object
        and confirms safe_stringify returns utf-8 encoding for all inputs
        """

        class testObject(object):
            def __str__(self):
                return "1"

        inputs = ["1", str(1), b"1", u"1", 1, testObject()]

        # confirm each input outputs unicode
        for value in inputs:
            safe_value = safe_stringify(value)
            self.assertEqual(safe_value, u"1")
            self.assertEqual(type(safe_value), six.text_type)
