from __future__ import print_function
import warnings

from globus_sdk import exc, config
from globus_sdk.base import BaseClient, merge_params
from globus_sdk.transfer.response import (
    TransferResponse, IterableTransferResponse)
from globus_sdk.transfer.paging import PaginatedResource


class TransferClient(BaseClient):
    """
    Client for the
    `Globus Transfer API <https://docs.globus.org/api/transfer/>`_.

    This class provides helper methods for most common resources in the
    REST API, and basic ``get``, ``put``, ``post``, and ``delete`` methods
    from the base rest client that can be used to access any REST resource.

    There are two types of helper methods: list methods which return an
    iterator of :class:`GlobusResponse \
    <globus_sdk.response.GlobusResponse>`
    objects, and simple methods that return a single
    :class:`TransferResponse <globus_sdk.transfer.response.TransferResponse>`
    object.

    Detailed documentation is available in the official REST API
    documentation, which is linked to from the method documentation. Methods
    that allow arbitrary keyword arguments will pass the extra arguments as
    query parameters.
    """

    error_class = exc.TransferAPIError
    default_response_class = TransferResponse

    def __init__(self, environment=config.get_default_environ(),
                 token=None, app_name=None):
        BaseClient.__init__(self, "transfer", environment, "/v0.10/",
                            token=token, app_name=None)

    def config_load_token(self):
        return config.get_transfer_token(self.environment)

    # Convenience methods, providing more pythonic access to common REST
    # resources

    #
    # Endpoint Management
    #

    def get_endpoint(self, endpoint_id, **params):
        """
        ``GET /endpoint/<endpoint_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        >>> tc = globus_sdk.TransferClient()
        >>> endpoint = tc.get_endpoint(endpoint_id)
        >>> print("Endpoint name:",
        >>>       endpoint["display_name"] or endpoint["canonical_name"])

        See
        `Get Endpoint by ID \
        <https://docs.globus.org/api/transfer/endpoint/#get_endpoint_by_id>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id)
        return self.get(path, params=params)

    def update_endpoint(self, endpoint_id, data, **params):
        """
        ``PUT /endpoint/<endpoint_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        >>> tc = globus_sdk.TransferClient()
        >>> epup = dict(display_name="My New Endpoint Name",
        >>>             description="Better Description")
        >>> update_result = tc.update_endpoint(endpoint_id, epup)

        See
        `Update Endpoint by ID \
        <https://docs.globus.org/api/transfer/endpoint/#update_endpoint_by_id>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id)
        return self.put(path, data, params=params)

    def create_endpoint(self, data):
        """
        ``POST /endpoint/<endpoint_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        >>> tc = globus_sdk.TransferClient()
        >>> ep_data = {
        >>>   "DATA_TYPE": "endpoint",
        >>>   "display_name": display_name,
        >>>   "DATA": [
        >>>     {
        >>>       "DATA_TYPE": "server",
        >>>       "hostname": "gridftp.example.edu",
        >>>     },
        >>>   ],
        >>> }
        >>> create_result = tc.create_shared_endpoint(ep_data)
        >>> endpoint_id = create_result["id"]

        See
        `Create endpoint \
        <https://docs.globus.org/api/transfer/endpoint/#create_endpoint>`_
        in the REST documentation for details.
        """
        return self.post("endpoint", data)

    def delete_endpoint(self, endpoint_id):
        """
        ``DELETE /endpoint/<endpoint_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        >>> tc = globus_sdk.TransferClient()
        >>> delete_result = tc.delete_endpoint(endpoint_id)

        See
        `Delete endpoint by id \
        <https://docs.globus.org/api/transfer/endpoint/#delete_endpoint_by_id>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id)
        return self.delete(path)

    def endpoint_manager_monitored_endpoints(self, **params):
        """
        ``GET endpoint_manager/monitored_endpoints``

        :rtype: iterable of :class:`GlobusResponse
                <globus_sdk.response.GlobusResponse>`
        """
        path = self.qjoin_path('endpoint_manager', 'monitored_endpoints')
        return self.get(path, params=params,
                        response_class=IterableTransferResponse)

    def endpoint_search(self, filter_fulltext=None, filter_scope=None,
                        num_results=25, **params):
        r"""
        .. parsed-literal::

            GET /endpoint_search\
            ?filter_fulltext=<filter_fulltext>&filter_scope=<filter_scope>

        :rtype: iterable of :class:`GlobusResponse
                <globus_sdk.response.GlobusResponse>`

        Search for a given string as a fulltext search:

        >>> tc = globus_sdk.TransferClient()
        >>> for ep in tc.endpoint_search('String to search for!'):
        >>>     print(ep['display_name'])

        Search for a given string, but only on endpoints that you own:

        >>> for ep in tc.endpoint_search('foo', filter_scope='my-endpoints'):
        >>>     print('{} has ID {}'.format(ep['display_name'], ep['id']))

        Search results are capped at a number of elements equal to the
        ``num_results`` parameter.
        If you want more than the default, 25, elements, do like so:

        >>> for ep in tc.endpoint_search('String to search for!',
        >>>                             num_results=120):
        >>>     print(ep['display_name'])

        It is important to be aware that the Endpoint Search API limits
        you to 1000 results for any search query.
        If you attempt to exceed this limit, you will trigger a
        :class:`PaginationOverrunError <globus_sdk.exc.PaginationOverrunError>`

        >>> for ep in tc.endpoint_search('globus', # a very common string
        >>>                             num_results=1200): # num too large!
        >>>     print(ep['display_name'])

        will trigger this error.

        For additional information, see `Endpoint Search
        <https://docs.globus.org/api/transfer/endpoint_search>`_.
        in the REST documentation for details.
        """
        merge_params(params, filter_scope=filter_scope,
                     filter_fulltext=filter_fulltext)
        return PaginatedResource(
            self.get, "endpoint_search", {'params': params},
            num_results=num_results, max_results_per_call=100,
            max_total_results=1000)

    def endpoint_autoactivate(self, endpoint_id, **params):
        r"""
        ``POST /endpoint/<endpoint_id>/autoactivate``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        The following example will try to "auto" activate the endpoint
        using a credential available from another endpoint or sign in by
        the user with the same identity provider, but only if the
        endpoint is not already activated or going to expire within an
        hour (3600 seconds). If that fails, direct the user to the
        globus website to perform activation:

        >>> tc = globus_sdk.TransferClient()
        >>> r = tc.endpoint_autoactivate(ep_id, if_expires_in=3600)
        >>> while (r["code"] == "AutoActivateFailed"):
        >>>     print("Endpoint requires manual activation, please open "
        >>>           "the following URL in a browser to activate the "
        >>>           "endpoint:")
        >>>     print("https://www.globus.org/app/endpoints/%s/activate"
        >>>           % ep_id)
        >>>     # For python 2.X, use raw_input() instead
        >>>     input("Press ENTER after activating the endpoint:")
        >>>     r = tc.endpoint_autoactivate(ep_id, if_expires_in=3600)

        This is the recommended flow for most thick client applications,
        because many endpoints require activation via OAuth MyProxy,
        which must be done in a browser anyway. Web based clients can
        link directly to the URL.

        See
        `Autoactivate endpoint \
        <https://docs.globus.org/api/transfer/endpoint_activation/#autoactivate_endpoint>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id, "autoactivate")
        return self.post(path, params=params)

    def endpoint_deactivate(self, endpoint_id, **params):
        """
        ``POST /endpoint/<endpoint_id>/deactivate``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Deactive endpoint \
        <https://docs.globus.org/api/transfer/endpoint_activation/#deactivate_endpoint>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id, "deactivate")
        return self.post(path, params=params)

    def endpoint_activate(self, endpoint_id, data, **params):
        """
        ``POST /endpoint/<endpoint_id>/activate``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        Consider using autoactivate and web activation instead, described
        in the example for
        :meth:`~globus_sdk.TransferClient.endpoint_autoactivate`.

        See
        `Activate endpoint \
        <https://docs.globus.org/api/transfer/endpoint_activation/#autoactivate_endpoint>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id, "autoactivate")
        return self.post(path, params=params)

    def endpoint_get_activation_requirements(self, endpoint_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/activation_requirements``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Get activation requirements \
        <https://docs.globus.org/api/transfer/endpoint_activation/#get_activation_requirements>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id, "autoactivate")
        return self.post(path, params=params)

    def my_effective_pause_rule_list(self, endpoint_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/my_effective_pause_rule_list``

        :rtype: :class:`IterableTransferResponse
                <globus_sdk.transfer.response.IterableTransferResponse>`

        See
        `Get my effective endpoint pause rules \
        <https://docs.globus.org/api/transfer/endpoint/#get_my_effective_endpoint_pause_rules>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path('endpoint', endpoint_id,
                               'my_effective_pause_rule_list')
        return self.get(path, params=params,
                        response_class=IterableTransferResponse)

    # Shared Endpoints

    def my_shared_endpoint_list(self, endpoint_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/my_shared_endpoint_list``

        :rtype: :class:`IterableTransferResponse
                <globus_sdk.transfer.response.IterableTransferResponse>`

        See
        `Get shared endpoint list \
        <https://docs.globus.org/api/transfer/endpoint/#get_shared_endpoint_list>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path('endpoint', endpoint_id,
                               'my_shared_endpoint_list')
        return self.get(path, params=params,
                        response_class=IterableTransferResponse)

    def create_shared_endpoint(self, data):
        """
        ``POST /shared_endpoint``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        :param data: A python dict representation of a ``shared_endpoint``
                     document

        >>> tc = globus_sdk.TransferClient()
        >>> shared_ep_data = {
        >>>   "DATA_TYPE": "shared_endpoint",
        >>>   "host_endpoint": host_endpoint_id,
        >>>   "host_path": host_path,
        >>>   "display_name": display_name,
        >>>   # optionally specify additional endpoint fields
        >>>   "description": "my test share"
        >>> }
        >>> create_result = tc.create_shared_endpoint(shared_ep_data)
        >>> endpoint_id = create_result["id"]

        See
        `Create shared endpoint \
        <https://docs.globus.org/api/transfer/endpoint/#create_shared_endpoint>`_
        in the REST documentation for details.
        """
        return self.post('shared_endpoint', json_body=data)

    # Endpoint servers

    def endpoint_server_list(self, endpoint_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/server_list``

        :rtype: :class:`IterableTransferResponse
                <globus_sdk.transfer.response.IterableTransferResponse>`

        See
        `Get endpoint server list \
        <https://docs.globus.org/api/transfer/endpoint/#get_endpoint_server_list>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'server_list')
        return self.get(path, params=params,
                        response_class=IterableTransferResponse)

    def get_endpoint_server(self, endpoint_id, server_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/server/<server_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Get endpoint server list \
        <https://docs.globus.org/api/transfer/endpoint/#get_endpoint_server_list>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id,
                               "server", str(server_id))
        return self.get(path, params=params)

    def add_endpoint_server(self, endpoint_id, server_data):
        """
        ``POST /endpoint/<endpoint_id>/server``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Add endpoint server \
        <https://docs.globus.org/api/transfer/endpoint/#add_endpoint_server>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id, "server")
        return self.post(path, server_data)

    def update_endpoint_server(self, endpoint_id, server_id, server_data):
        """
        ``PUT /endpoint/<endpoint_id>/server/<server_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Update endpoint server by id \
        <https://docs.globus.org/api/transfer/endpoint/#update_endpoint_server_by_id>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id,
                               "server", str(server_id))
        return self.put(path, server_data)

    def delete_endpoint_server(self, endpoint_id, server_id):
        """
        ``DELETE /endpoint/<endpoint_id>/server/<server_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Delete endpoint server by id \
        <https://docs.globus.org/api/transfer/endpoint/#delete_endpoint_server_by_id>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("endpoint", endpoint_id,
                               "server", str(server_id))
        return self.delete(path)

    #
    # Roles
    #

    def endpoint_role_list(self, endpoint_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/role_list``

        :rtype: :class:`IterableTransferResponse
                <globus_sdk.transfer.response.IterableTransferResponse>`

        See
        `Get list of endpoint roles \
        <https://docs.globus.org/api/transfer/endpoint_roles/#get_list_of_endpoint_roles>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'role_list')
        return self.get(path, params=params,
                        response_class=IterableTransferResponse)

    def add_endpoint_role(self, endpoint_id, role_data):
        """
        ``POST /endpoint/<endpoint_id>/role``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Create endpoint role \
        <https://docs.globus.org/api/transfer/endpoint_roles/#create_endpoint_role>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'role')
        return self.post(path, role_data)

    def get_endpoint_role(self, endpoint_id, role_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/role/<role_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Get endpoint role by id \
        <https://docs.globus.org/api/transfer/endpoint_roles/#get_endpoint_role_by_id>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'role', role_id)
        return self.get(path, params=params)

    def delete_endpoint_role(self, endpoint_id, role_id):
        """
        ``DELETE /endpoint/<endpoint_id>/role/<role_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        See
        `Delete endpoint role by id \
        <https://docs.globus.org/api/transfer/endpoint_roles/#delete_endpoint_role_by_id>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'role', role_id)
        return self.delete(path)

    #
    # ACLs
    #

    def endpoint_acl_list(self, endpoint_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/access_list``

        :rtype: :class:`IterableTransferResponse
                <globus_sdk.transfer.response.IterableTransferResponse>`
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'access_list')
        return self.get(path, params=params,
                        response_class=IterableTransferResponse)

    def get_endpoint_acl_rule(self, endpoint_id, rule_id, **params):
        """
        ``GET /endpoint/<endpoint_id>/access/<rule_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'access', rule_id)
        return self.get(path, params=params)

    def add_endpoint_acl_rule(self, endpoint_id, rule_data):
        """
        ``POST /endpoint/<endpoint_id>/access``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'access')
        return self.post(path, rule_data)

    def update_endpoint_acl_rule(self, endpoint_id, rule_id, rule_data):
        """
        ``PUT /endpoint/<endpoint_id>/access/<rule_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'access', rule_id)
        return self.put(path, rule_data)

    def delete_endpoint_acl_rule(self, endpoint_id, rule_id):
        """
        ``DELETE /endpoint/<endpoint_id>/access/<rule_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        path = self.qjoin_path('endpoint', endpoint_id, 'access', rule_id)
        return self.delete(path)

    #
    # Bookmarks
    #

    def bookmark_list(self, **params):
        """
        ``GET /bookmark_list``

        :rtype: :class:`IterableTransferResponse
                <globus_sdk.transfer.response.IterableTransferResponse>`
        """
        return self.get('bookmark_list', params=params,
                        response_class=IterableTransferResponse)

    def create_bookmark(self, bookmark_data):
        """
        ``POST /bookmark``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        return self.post('bookmark', bookmark_data)

    def get_bookmark(self, bookmark_id, **params):
        """
        ``GET /bookmark/<bookmark_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        path = self.qjoin_path('bookmark', bookmark_id)
        return self.get(path, params=params)

    def update_bookmark(self, bookmark_id, bookmark_data):
        """
        ``PUT /bookmark/<bookmark_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        path = self.qjoin_path('bookmark', bookmark_id)
        return self.put(path, bookmark_data)

    def delete_bookmark(self, bookmark_id):
        """
        ``DELETE /bookmark/<bookmark_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        path = self.qjoin_path('bookmark', bookmark_id)
        return self.delete(path)

    #
    # Synchronous Filesys Operations
    #

    def operation_ls(self, endpoint_id, **params):
        """
        ``GET /operation/endpoint/<endpoint_id>/ls``

        :rtype: :class:`IterableTransferResponse
                <globus_sdk.transfer.response.IterableTransferResponse>`

        >>> tc = globus_sdk.TransferClient()
        >>> for entry in tc.operation_ls(ep_id, path="/~/project1/"):
        >>>     print(entry["name"], entry["type"])

        See
        `List Directory Contents \
        <https://docs.globus.org/api/transfer/file_operations/#list_directory_contents>`_
        in the REST documentation for details.
        """
        path = self.qjoin_path("operation/endpoint", endpoint_id, "ls")
        return self.get(path, params=params,
                        response_class=IterableTransferResponse)

    def operation_mkdir(self, endpoint_id, path, **params):
        """
        ``POST /operation/endpoint/<endpoint_id>/mkdir``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        >>> tc = globus_sdk.TransferClient()
        >>> tc.operation_mkdir(ep_id, path="/~/newdir/")

        See
        `Make Directory \
        <https://docs.globus.org/api/transfer/file_operations/#make_directory>`_
        in the REST documentation for details.
        """
        resource_path = self.qjoin_path("operation/endpoint", endpoint_id,
                                        "mkdir")
        json_body = {
            'DATA_TYPE': 'mkdir',
            'path': path
        }
        return self.post(resource_path, json_body=json_body, params=params)

    def operation_rename(self, endpoint_id, oldpath, newpath, **params):
        """
        ``POST /operation/endpoint/<endpoint_id>/rename``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        >>> tc = globus_sdk.TransferClient()
        >>> tc.operation_rename(ep_id, oldpath="/~/file1.txt",
        >>>                     newpath="/~/project1data.txt")

        See
        `Rename \
        <https://docs.globus.org/api/transfer/file_operations/#rename>`_
        in the REST documentation for details.
        """
        resource_path = self.qjoin_path("operation/endpoint", endpoint_id,
                                        "rename")
        json_body = {
            'DATA_TYPE': 'mkdir',
            'old_path': oldpath,
            'new_path': newpath
        }
        return self.post(resource_path, json_body=json_body, params=params)

    #
    # Task Submission
    #

    def get_submission_id(self, **params):
        """
        ``GET /submission_id``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        return self.get("submission_id", params=params)

    def submit_transfer(self, data):
        """
        ``POST /transfer``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        Example usage:

        >>> tc = globus_sdk.TransferClient()
        >>> tdata = globus_sdk.TransferData(tc, source_endpoint_id,
        >>>                                 destination_endpoint_id,
        >>>                                 label="SDK example",
        >>>                                 sync_level="checksum")
        >>> tdata.add_item("/source/path/dir/", "/dest/path/dir/",
        >>>                recursive=True)
        >>> tdata.add_item("/source/path/file.txt",
        >>>                "/dest/path/file.txt")
        >>> transfer_result = tc.submit_transfer(tdata)
        >>> print("task_id =", transfer_result["task_id"])

        The `data` parameter can be a normal Python dictionary, or
        a :class:`TransferData <globus_sdk.TransferData>` object.

        See
        `Submit a transfer task \
        <https://docs.globus.org/api/transfer/task_submit/#submit_a_transfer_task>`_
        in the REST documentation for more details.
        """
        return self.post('/transfer', data)

    def submit_delete(self, data):
        """
        ``POST /delete``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`

        Example usage:

        >>> tc = globus_sdk.TransferClient()
        >>> ddata = globus_sdk.DeleteData(tc, endpoint_id, recursive=True)
        >>> ddata.add_item("/dir/to/delete/")
        >>> ddata.add_item("/file/to/delete/file.txt")
        >>> delete_result = tc.submit_delete(ddata)
        >>> print("task_id =", delete_result["task_id"])

        The `data` parameter can be a normal Python dictionary, or
        a :class:`DeleteData <globus_sdk.DeleteData>` object.

        See
        `Submit a delete task \
        <https://docs.globus.org/api/transfer/task_submit/#submit_a_delete_task>`_
        in the REST documentation for details.
        """
        return self.post('/delete', data)

    def make_submit_transfer_data(self, source_endpoint, dest_endpoint,
                                  transfer_items, label=None, sync_level=None,
                                  **kwargs):
        """
        DEPRECATED: Use :class:`TransferData <globus_sdk.TransferData>`
        instead.
        """
        warnings.warn(("make_submit_transfer_data() is deprecated. Use "
                       "globus_sdk.TransferData instead."), DeprecationWarning)
        datadoc = {
            'DATA_TYPE': 'transfer',
            'submission_id': self.get_submission_id()['value'],
            'source_endpoint': source_endpoint,
            'destination_endpoint': dest_endpoint,
            'DATA': transfer_items
        }

        # map the sync_level (if it's a nice string) to one of the known int
        # values
        # you can get away with specifying an invalid sync level -- the API
        # will just reject you with an error. This is kind of important: if
        # more levels are added in the future this method doesn't become
        # garbage overnight
        if sync_level is not None:
            sync_dict = {"exists": 1, "mtime": 2, "checksum": 3}
            sync_level = sync_dict.get(sync_level, sync_level)
            datadoc['sync_level'] = sync_level

        if label is not None:
            datadoc['label'] = label

        # any remaining arguments are global options for the Transfer document
        # pass them through verbatim
        for optional_arg in kwargs:
            datadoc[optional_arg] = kwargs[optional_arg]

        return datadoc

    def make_submit_transfer_item(self, source, dest, recursive=False):
        """
        DEPRECATED: Use :class:`TransferData <globus_sdk.TransferData>`
        instead.
        """
        warnings.warn(("make_submit_transfer_item() is deprecated. Use "
                       "globus_sdk.TransferData instead."), DeprecationWarning)
        datadoc = {
            'DATA_TYPE': 'transfer_item',
            'source_path': source,
            'destination_path': dest
        }
        if recursive:
            datadoc['recursive'] = True

        return datadoc

    #
    # Task inspection and management
    #

    def endpoint_manager_task_list(self, num_results=10, **params):
        """
        ``GET endpoint_manager/task_list``

        :rtype: iterable of :class:`GlobusResponse
                <globus_sdk.response.GlobusResponse>`
        """
        path = self.qjoin_path('endpoint_manager', 'task_list')
        return PaginatedResource(
            self.get, path, {'params': params},
            num_results=num_results, max_results_per_call=1000,
            paging_style=PaginatedResource.PAGING_STYLE_HAS_NEXT)

    def task_list(self, num_results=10, **params):
        """
        ``GET /task_list``

        :rtype: iterable of :class:`GlobusResponse
                <globus_sdk.response.GlobusResponse>`
        """
        return PaginatedResource(
            self.get, 'task_list', {'params': params},
            num_results=num_results, max_results_per_call=1000,
            paging_style=PaginatedResource.PAGING_STYLE_TOTAL)

    def task_event_list(self, task_id, num_results=10, **params):
        """
        ``GET /task/<task_id>/event_list``

        :rtype: iterable of :class:`GlobusResponse
                <globus_sdk.response.GlobusResponse>`
        """
        path = self.qjoin_path('task', task_id, 'event_list')
        return PaginatedResource(
            self.get, path, {'params': params},
            num_results=num_results, max_results_per_call=1000,
            paging_style=PaginatedResource.PAGING_STYLE_TOTAL)

    def get_task(self, task_id, **params):
        """
        ``GET /task/<task_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        resource_path = self.qjoin_path("task", task_id)
        return self.get(resource_path, params=params)

    def update_task(self, task_id, data, **params):
        """
        ``PUT /task/<task_id>``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        resource_path = self.qjoin_path("task", task_id)
        return self.put(resource_path, data, params=params)

    def cancel_task(self, task_id):
        """
        ``POST /task/<task_id>/cancel``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        resource_path = self.qjoin_path("task", task_id, "cancel")
        return self.post(resource_path)

    def task_pause_info(self, task_id, **params):
        """
        ``POST /task/<task_id>/pause_info``

        :rtype: :class:`TransferResponse
                <globus_sdk.transfer.response.TransferResponse>`
        """
        resource_path = self.qjoin_path("task", task_id, "pause_info")
        return self.get(resource_path, params=params)
