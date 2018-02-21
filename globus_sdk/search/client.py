from __future__ import unicode_literals
import logging

from globus_sdk import exc
from globus_sdk.base import BaseClient, merge_params, safe_stringify
from globus_sdk.authorizers import (
    AccessTokenAuthorizer, RefreshTokenAuthorizer, ClientCredentialsAuthorizer)
from globus_sdk.response import GlobusHTTPResponse

logger = logging.getLogger(__name__)


class SearchClient(BaseClient):
    r"""
    Client for the Globus Search API

    This class provides helper methods for most common resources in the
    API, and basic ``get``, ``put``, ``post``, and ``delete`` methods
    from the base client that can be used to access any API resource.

    **Parameters**

        ``authorizer`` (:class:`GlobusAuthorizer\
        <globus_sdk.authorizers.base.GlobusAuthorizer>`)

          An authorizer instance used for all calls to Globus Search
    """
    # disallow basic auth
    allowed_authorizer_types = [AccessTokenAuthorizer,
                                RefreshTokenAuthorizer,
                                ClientCredentialsAuthorizer]
    error_class = exc.SearchAPIError
    default_response_class = GlobusHTTPResponse

    def __init__(self, authorizer=None, **kwargs):
        BaseClient.__init__(self, "search", authorizer=authorizer, **kwargs)

    #
    # Index Management
    #

    def get_index(self, index_id, **params):
        """
        ``GET /v1/index/<index_id>``

        **Examples**

        >>> sc = globus_sdk.SearchClient(...)
        >>> index = sc.get_index(index_id)
        >>> assert index['index_id'] == index_id
        >>> print(index["display_name"],
        >>>       "(" + index_id + "):",
        >>>       index["description"])

        **External Documentation**

        See
        `Get Index Metadata \
        <https://docs.globus.org/api/search/index_meta/>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        self.logger.info("SearchClient.get_index({0})".format(index_id))
        path = self.qjoin_path("v1/index", index_id)
        return self.get(path, params=params)

    #
    # Search queries
    #

    def search(self, index_id, q, offset=0, limit=10, query_template=None,
               advanced=False, **params):
        """
        ``GET /v1/index/<index_id>/search``

        **Examples**

        >>> sc = globus_sdk.SearchClient(...)
        >>> result = sc.search(index_id, 'query string')
        >>> advanced_result = sc.search(index_id, 'author: "Ada Lovelace"',
        >>>                             advanced=True)

        **External Documentation**

        See
        `GET Search Query \
        <https://docs.globus.org/api/search/search/#simple_get_query>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        merge_params(params, q=q, offset=offset, limit=limit,
                     query_template=query_template, advanced=advanced)

        self.logger.info("SearchClient.search({0}, ...)"
                         .format(index_id))
        path = self.qjoin_path("v1/index", index_id, "search")
        return self.get(path, params=params)

    def post_search(self, index_id, data):
        """
        ``POST /v1/index/<index_id>/search``

        **Examples**

        >>> sc = globus_sdk.SearchClient(...)
        >>> query_data = {
        >>>   "@datatype": "GSearchRequest",
        >>>   "q": "user query",
        >>>   "filters": [
        >>>     {
        >>>       "type": "range",
        >>>       "field_name": "path.to.date",
        >>>       "values": [
        >>>         {"from": "*",
        >>>          "to": "2014-11-07"}
        >>>       ]
        >>>     }
        >>>   ],
        >>>   "facets": [
        >>>     {"name": "Publication Date",
        >>>      "field_name": "path.to.date",
        >>>      "type": "date_histogram",
        >>>      "date_interval": "year"}
        >>>   ],
        >>>   "sort": [
        >>>     {"field_name": "path.to.date",
        >>>      "order": "asc"}
        >>>   ]
        >>> }
        >>> search_result = sc.post_search(index_id, query_data)

        **External Documentation**

        See
        `POST Search Query \
        <https://docs.globus.org/api/search/search/#complex_post_query>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        self.logger.info("SearchClient.post_search({0}, ...)"
                         .format(index_id))
        path = self.qjoin_path("v1/index", index_id, "search")
        return self.post(path, data)

    #
    # Bulk data indexing
    #

    def ingest(self, index_id, data):
        """
        ``POST /v1/index/<index_id>/ingest``

        **Examples**

        >>> sc = globus_sdk.SearchClient(...)
        >>> ingest_data = {
        >>>   "ingest_type": "GMetaEntry",
        >>>   "ingest_data": {
        >>>     "subject": "https://example.com/foo/bar",
        >>>     "visible_to": ["public"],
        >>>     "content": {
        >>>       "foo/bar": "some val"
        >>>     }
        >>>   }
        >>> }
        >>> sc.ingest(index_id, ingest_data)

        or with multiple entries at once via a GMetaList:

        >>> sc = globus_sdk.SearchClient(...)
        >>> ingest_data = {
        >>>   "ingest_type": "GMetaList",
        >>>   "ingest_data": {
        >>>     "gmeta": [
        >>>       {
        >>>         "subject": "https://example.com/foo/bar",
        >>>         "visible_to": ["public"],
        >>>         "content": {
        >>>           "foo/bar": "some val"
        >>>         }
        >>>       },
        >>>       {
        >>>         "subject": "https://example.com/foo/bar",
        >>>         "id": "otherentry",
        >>>         "visible_to": ["public"],
        >>>         "content": {
        >>>           "foo/bar": "some otherval"
        >>>         }
        >>>       }
        >>>     ]
        >>>   }
        >>> }
        >>> sc.ingest(index_id, ingest_data)

        **External Documentation**

        See
        `Ingest \
        <https://docs.globus.org/api/search/ingest/>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        self.logger.info("SearchClient.ingest({0}, ...)".format(index_id))
        path = self.qjoin_path("v1/index", index_id, "ingest")
        return self.post(path, data)

    #
    # Bulk delete
    #

    def delete_by_query(self, index_id, data):
        """
        ``POST /v1/index/<index_id>/delete_by_query``

        **Examples**

        >>> sc = globus_sdk.SearchClient(...)
        >>> query_data = {
        >>>   "q": "user query",
        >>>   "filters": [
        >>>     {
        >>>       "type": "range",
        >>>       "field_name": "path.to.date",
        >>>       "values": [
        >>>         {"from": "*",
        >>>          "to": "2014-11-07"}
        >>>       ]
        >>>     }
        >>>   ]
        >>> }
        >>> sc.delete_by_query(index_id, query_data)

        **External Documentation**

        See
        `Delete By Query \
        <https://docs.globus.org/api/search/subject_ops/#delete_by_query>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        self.logger.info("SearchClient.delete_by_query({0}, ...)"
                         .format(index_id))
        path = self.qjoin_path("v1/index", index_id, "delete_by_query")
        return self.post(path, data)

    #
    # Subject Operations
    #

    def get_subject(self, index_id, subject, **params):
        """
        ``GET /v1/index/<index_id>/subject``

        **Examples**

        Fetch the data for subject ``http://example.com/abc`` from index
        ``index_id``:

        >>> sc = globus_sdk.SearchClient(...)
        >>> subject_data = sc.get_subject(index_id, 'http://example.com/abc')

        **External Documentation**

        See
        `Get Subject \
        <https://docs.globus.org/api/search/subject_ops/#get_by_subject>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        merge_params(params, subject=subject)

        self.logger.info("SearchClient.get_subject({0}, {1}, ...)"
                         .format(index_id, subject))
        path = self.qjoin_path("v1/index", index_id, "subject")
        return self.get(path, params=params)

    def delete_subject(self, index_id, subject, **params):
        """
        ``DELETE /v1/index/<index_id>/subject``

        **Examples**

        Delete all data for subject ``http://example.com/abc`` from index
        ``index_id``, even data which is not visible to the current user:

        >>> sc = globus_sdk.SearchClient(...)
        >>> subject_data = sc.get_subject(index_id, 'http://example.com/abc')

        **External Documentation**

        See
        `Delete Subject \
        <https://docs.globus.org/api/search/subject_ops/#delete_by_subject>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        merge_params(params, subject=subject)

        self.logger.info("SearchClient.delete_subject({0}, {1}, ...)"
                         .format(index_id, subject))
        path = self.qjoin_path("v1/index", index_id, "subject")
        return self.delete(path, params=params)

    #
    # Entry Operations
    #

    def get_entry(self, index_id, subject, entry_id=None, **params):
        """
        ``GET /v1/index/<index_id>/entry``

        **Examples**

        Lookup the entry with a subject of ``https://example.com/foo/bar`` and
        a null entry_id:

        >>> sc = globus_sdk.SearchClient(...)
        >>> entry_data = sc.get_entry(index_id, 'http://example.com/foo/bar')

        Lookup the entry with a subject of ``https://example.com/foo/bar`` and
        an entry_id of ``foo/bar``:

        >>> sc = globus_sdk.SearchClient(...)
        >>> entry_data = sc.get_entry(index_id, 'http://example.com/foo/bar',
        >>>                           entry_id='foo/bar')

        **External Documentation**

        See
        `Get Entry \
        <https://docs.globus.org/api/search/entry_ops/#get_single_entry>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        merge_params(params, subject=subject, entry_id=entry_id)

        self.logger.info("SearchClient.get_entry({0}, {1}, {2}, ...)"
                         .format(index_id, subject, entry_id))
        path = self.qjoin_path("v1/index", index_id, "entry")
        return self.get(path, params=params)

    def create_entry(self, index_id, data):
        """
        ``POST /v1/index/<index_id>/entry``

        **Examples**

        Create an entry with a subject of ``https://example.com/foo/bar`` and
        a null entry_id:

        >>> sc = globus_sdk.SearchClient(...)
        >>> sc.create_entry(index_id, {
        >>>     "subject": "https://example.com/foo/bar",
        >>>     "visible_to": ["public"],
        >>>     "content": {
        >>>         "foo/bar": "some val"
        >>>     }
        >>> })

        Create an entry with a subject of ``https://example.com/foo/bar`` and
        an entry_id of ``foo/bar``:

        >>> sc = globus_sdk.SearchClient(...)
        >>> sc.create_entry(index_id, {
        >>>     "subject": "https://example.com/foo/bar",
        >>>     "visible_to": ["public"],
        >>>     "id": "foo/bar",
        >>>     "content": {
        >>>         "foo/bar": "some val"
        >>>     }
        >>> })

        **External Documentation**

        See
        `Create Entry \
        <https://docs.globus.org/api/search/entry_ops/#create_single_entry>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        self.logger.info("SearchClient.create_entry({0}, ...)"
                         .format(index_id))
        path = self.qjoin_path("v1/index", index_id, "entry")
        return self.post(path, data)

    def update_entry(self, index_id, data):
        """
        ``PUT /v1/index/<index_id>/entry``

        **Examples**

        Update an entry with a subject of ``https://example.com/foo/bar`` and
        a null entry_id:

        >>> sc = globus_sdk.SearchClient(...)
        >>> sc.update_entry(index_id, {
        >>>     "subject": "https://example.com/foo/bar",
        >>>     "visible_to": ["public"],
        >>>     "content": {
        >>>         "foo/bar": "some val"
        >>>     }
        >>> })

        **External Documentation**

        See
        `Update Entry \
        <https://docs.globus.org/api/search/entry_ops/#update_single_entry>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        self.logger.info("SearchClient.update_entry({0}, ...)"
                         .format(index_id))
        path = self.qjoin_path("v1/index", index_id, "entry")
        return self.put(path, data)

    def delete_entry(self, index_id, subject, entry_id=None, **params):
        """
        ``DELETE  /v1/index/<index_id>/entry``

        **Examples**

        Delete an entry with a subject of ``https://example.com/foo/bar`` and
        a null entry_id:

        >>> sc = globus_sdk.SearchClient(...)
        >>> sc.delete_entry(index_id, "https://example.com/foo/bar")

        Delete an entry with a subject of ``https://example.com/foo/bar`` and
        an entry_id of "foo/bar":

        >>> sc = globus_sdk.SearchClient(...)
        >>> sc.delete_entry(index_id, "https://example.com/foo/bar",
        >>>                 entry_id="foo/bar")

        **External Documentation**

        See
        `Delete Entry \
        <https://docs.globus.org/api/search/entry_ops/#delete_single_entry>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        merge_params(params, subject=subject, entry_id=entry_id)
        self.logger.info("SearchClient.delete_entry({0}, {1}, {2}, ...)"
                         .format(index_id, subject, entry_id))
        path = self.qjoin_path("v1/index", index_id, "entry")
        return self.delete(path, params=params)

    #
    # Lookup Query Templates
    #

    def get_query_template(self, index_id, template_name):
        """
        ``GET /v1/index/<index_id>/query_template/<template_name>``

        **External Documentation**

        See
        `Get Query Template \
        <https://docs.globus.org/api/search/query_templates/#get_query_template>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        self.logger.info("SearchClient.get_query_template({0}, {1})"
                         .format(index_id, template_name))
        path = self.qjoin_path("v1/index", index_id, "query_template",
                               template_name)
        return self.get(path)

    def get_query_template_list(self, index_id):
        """
        ``GET /v1/index/<index_id>/query_template``

        **External Documentation**

        See
        `Get Query Template List \
        <https://docs.globus.org/api/search/query_templates/#get_query_template_list>`_
        in the API documentation for details.
        """
        index_id = safe_stringify(index_id)
        self.logger.info("SearchClient.get_query_template_list({0})"
                         .format(index_id))
        path = self.qjoin_path("v1/index", index_id, "query_template")
        return self.get(path)
