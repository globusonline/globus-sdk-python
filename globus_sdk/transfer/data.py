"""
Data helper classes for constructing Transfer API documents. All classes should
extend ``dict``, so they can be passed seamlessly to
:class:`TransferClient <globus_sdk.TransferClient>` methods without
conversion.
"""
from __future__ import unicode_literals
import logging

from globus_sdk.base import safe_stringify

logger = logging.getLogger(__name__)


class TransferData(dict):
    """
    Convenience class for constructing a transfer document, to use as the
    `data` parameter to
    :meth:`submit_transfer <globus_sdk.TransferClient.submit_transfer>`.

    At least one item must be added using
    :meth:`add_item <globus_sdk.TransferData.add_item>`.

    If ``submission_id`` isn't passed, one will be fetched automatically. The
    submission ID can be pulled out of here to inspect, but the document
    can be used as-is multiple times over to retry a potential submission
    failure (so there shouldn't be any need to inspect it).

    **Parameters**

      ``transfer_client`` (:class:`TransferClient <globus_sdk.TransferClient>`)
        A ``TransferClient`` instance which will be used to get a submission ID
        if one is not supplied. Should be the same instance that is used to
        submit the transfer.

      ``source_endpoint`` (*string*)
        The endpoint ID of the source endpoint

      ``destination_endpoint`` (*string*)
        The endpoint ID of the destination endpoint

      ``label`` (*string*) [optional]
        A string label for the Task

      ``submission_id`` (*string*) [optional]
        A submission ID value fetched via
        :meth:`get_submission_id \
        <globus_sdk.TransferClient.get_submission_id>`. Defaults to using
        ``transfer_client.get_submission_id``

      ``sync_level`` (*int* or *string*) [optional]
        For compatibility with older code and those knowledgeable about the API
        sync_level can be ``0``, ``1``, ``2``, or ``3``, but it can also be
        ``"exists"``, ``"size"``, ``"mtime"``, or ``"checksum"`` if you want
        greater clarity in client code.

      ``verify_checksum`` (*bool*) [default: ``False``]
        When true, perform additional integrity checks on each file after it is
        transferred. This will create CPU load on both the origin and
        destination of the transfer, and may even be a bottleneck if the
        network speed is high enough.

      ``preserve_timestamp`` (*bool*) [default: ``False``]
        When true, Globus Transfer will attempt to set file timestamps on the
        destination to match those on the origin.

      ``encrypt_data`` (*bool*) [default: ``False``]
        When true, all files will be TLS-protected during transfer.

      ``deadline`` (*string* or *datetime*) [optional]
        An ISO-8601 timestamp (as a string) or a datetime object which defines
        a deadline for the transfer. At the deadline, even if the data transfer
        is not complete, the job will be canceled.
        We recommend ensuring that the timestamp is in UTC to avoid confusion
        and ambiguity.

        Examples of ISO-8601 timestamps include ``2017-10-12 09:30Z``,
        ``2017-10-12 12:33:54+00:00``, and ``2017-10-12``

      ``recursive_symlinks`` (*string*) [default: ``"ignore"``]
        Specify the behavior of recursive directory transfers when encountering
        symlinks. One of ``"ignore"``, ``"keep"``, or ``"copy"``. ``"ignore"``
        skips symlinks, ``"keep"`` creates symlinks at the destination matching
        the source (without modifying the link path at all), and ``"copy"``
        follows symlinks on the source, failing if the link is invalid.

    Any additional parameters are fed into the dict being created verbatim.

    **Examples**

    See the
    :meth:`submit_transfer <globus_sdk.TransferClient.submit_transfer>`
    documentation for example usage.
    """
    def __init__(self, transfer_client, source_endpoint, destination_endpoint,
                 label=None, submission_id=None, sync_level=None,
                 verify_checksum=False, preserve_timestamp=False,
                 encrypt_data=False, deadline=None,
                 recursive_symlinks="ignore", **kwargs):
        source_endpoint = safe_stringify(source_endpoint)
        destination_endpoint = safe_stringify(destination_endpoint)
        logger.info("Creating a new TransferData object")
        self["DATA_TYPE"] = "transfer"
        self["submission_id"] = submission_id or \
            transfer_client.get_submission_id()["value"]
        logger.info("TransferData.submission_id = {0}"
                    .format(self["submission_id"]))
        self["source_endpoint"] = source_endpoint
        logger.info("TransferData.source_endpoint = {0}"
                    .format(source_endpoint))
        self["destination_endpoint"] = destination_endpoint
        logger.info("TransferData.destination_endpoint = {0}"
                    .format(destination_endpoint))
        self["verify_checksum"] = verify_checksum
        logger.info("TransferData.verify_checksum = {0}"
                    .format(verify_checksum))
        self["preserve_timestamp"] = preserve_timestamp
        logger.info("TransferData.preserve_timestamp = {0}"
                    .format(preserve_timestamp))
        self["encrypt_data"] = encrypt_data
        logger.info("TransferData.encrypt_data = {0}"
                    .format(encrypt_data))
        self["recursive_symlinks"] = recursive_symlinks
        logger.info("TransferData.recursive_symlinks = {0}"
                    .format(recursive_symlinks))

        if label is not None:
            self["label"] = label
            logger.debug("TransferData.label = {0}".format(label))

        if deadline is not None:
            self["deadline"] = str(deadline)
            logger.debug("TransferData.deadline = {0}".format(deadline))

        # map the sync_level (if it's a nice string) to one of the known int
        # values
        # you can get away with specifying an invalid sync level -- the API
        # will just reject you with an error. This is kind of important: if
        # more levels are added in the future this method doesn't become
        # garbage overnight
        if sync_level is not None:
            sync_dict = {"exists": 0, "size": 1, "mtime": 2, "checksum": 3}
            self['sync_level'] = sync_dict.get(sync_level, sync_level)
            logger.info("TransferData.sync_level = {0} ({1})"
                        .format(self['sync_level'], sync_level))

        self["DATA"] = []

        self.update(kwargs)
        for option, value in kwargs.items():
            logger.info("TransferData.{0} = {1} (option passed in via kwargs)"
                        .format(option, value))

    def add_item(self, source_path, destination_path, recursive=False):
        """
        Add a file or directory to be transfered. If the item is a symlink
        to a file or directory, the file or directory at the target of
        the symlink will be transfered.

        Appends a transfer_item document to the DATA key of the transfer
        document.
        """
        source_path = safe_stringify(source_path)
        destination_path = safe_stringify(destination_path)
        item_data = {
            "DATA_TYPE": "transfer_item",
            "source_path": source_path,
            "destination_path": destination_path,
            "recursive": recursive,
        }
        logger.debug('TransferData[{0}, {1}].add_item: "{2}"->"{3}"'
                     .format(self["source_endpoint"],
                             self["destination_endpoint"],
                             source_path, destination_path))
        self["DATA"].append(item_data)

    def add_symlink_item(self, source_path, destination_path):
        """
        Add a symlink to be transfered as a symlink rather than as the
        target of the symlink.

        Appends a transfer_symlink_item document to the DATA key of the
        transfer document.
        """
        source_path = safe_stringify(source_path)
        destination_path = safe_stringify(destination_path)
        item_data = {
            "DATA_TYPE": "transfer_symlink_item",
            "source_path": source_path,
            "destination_path": destination_path,
        }
        logger.debug('TransferData[{0}, {1}].add_symlink_item: "{2}"->"{3}"'
                     .format(self["source_endpoint"],
                             self["destination_endpoint"],
                             source_path, destination_path))
        self["DATA"].append(item_data)


class DeleteData(dict):
    """
    Convenience class for constructing a delete document, to use as the
    `data` parameter to
    :meth:`submit_delete <globus_sdk.TransferClient.submit_delete>`.

    At least one item must be added using
    :meth:`add_item <globus_sdk.DeleteData.add_item>`.

    If ``submission_id`` isn't passed, one will be fetched automatically. The
    submission ID can be pulled out of here to inspect, but the document
    can be used as-is multiple times over to retry a potential submission
    failure (so there shouldn't be any need to inspect it).

    **Parameters**

      ``transfer_client`` (:class:`TransferClient <globus_sdk.TransferClient>`)
        A ``TransferClient`` instance which will be used to get a submission ID
        if one is not supplied. Should be the same instance that is used to
        submit the deletion.

      ``endpoint`` (*string*)
        The endpoint ID which is targeted by this deletion Task

      ``label`` (*string*) [optional]
        A string label for the Task

      ``submission_id`` (*string*) [optional]
        A submission ID value fetched via
        :meth:`get_submission_id \
        <globus_sdk.TransferClient.get_submission_id>`. Defaults to using
        ``transfer_client.get_submission_id``

      ``recursive`` (*bool*) [default: ``False``]
        Recursively delete subdirectories on the target endpoint

      ``deadline`` (*string* or *datetime*) [optional]
        An ISO-8601 timestamp (as a string) or a datetime object which defines
        a deadline for the transfer. At the deadline, even if the data deletion
        is not complete, the job will be canceled.
        We recommend ensuring that the timestamp is in UTC to avoid confusion
        and ambiguity.

        Examples of ISO-8601 timestamps include ``2017-10-12 09:30Z``,
        ``2017-10-12 12:33:54+00:00``, and ``2017-10-12``

    **Examples**

    See the :meth:`submit_delete <globus_sdk.TransferClient.submit_delete>`
    documentation for example usage.
    """
    def __init__(self, transfer_client, endpoint, label=None,
                 submission_id=None, recursive=False, deadline=None, **kwargs):
        endpoint = safe_stringify(endpoint)
        logger.info("Creating a new DeleteData object")
        self["DATA_TYPE"] = "delete"
        self["submission_id"] = submission_id or \
            transfer_client.get_submission_id()["value"]
        logger.info("DeleteData.submission_id = {0}"
                    .format(self["submission_id"]))
        self["endpoint"] = endpoint
        logger.info("DeleteData.endpoint = {0}"
                    .format(endpoint))
        self["recursive"] = recursive
        logger.info("DeleteData.recursive = {0}"
                    .format(recursive))

        if label is not None:
            self["label"] = label
            logger.debug("DeleteData.label = {0}".format(label))

        if deadline is not None:
            self["deadline"] = str(deadline)
            logger.debug("DeleteData.deadline = {0}".format(deadline))

        self["DATA"] = []

        self.update(kwargs)
        for option, value in kwargs.items():
            logger.info("DeleteData.{0} = {1} (option passed in via kwargs)"
                        .format(option, value))

    def add_item(self, path):
        """
        Add a file or directory or symlink to be deleted. If any of the paths
        are directories, ``recursive`` must be set True on the top level
        ``DeleteData``. Symlinks will never be followed, only deleted.

        Appends a delete_item document to the DATA key of the delete
        document.
        """
        path = safe_stringify(path)
        item_data = {
            "DATA_TYPE": "delete_item",
            "path": path,
        }
        logger.debug('DeleteData[{0}].add_item: "{1}"'
                     .format(self["endpoint"], path))
        self["DATA"].append(item_data)
