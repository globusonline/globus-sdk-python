"""
Data helper classes for constructing Transfer API documents. All classes should
extend ``dict``, so they can be passed seamlessly to
:class:`TransferClient <globus_sdk.TransferClient>` methods without
conversion.
"""

import logging

from globus_sdk.base import safe_stringify

logger = logging.getLogger(__name__)


class TransferData(dict):
    r"""
    Convenience class for constructing a transfer document, to use as the
    `data` parameter to
    :meth:`submit_transfer <globus_sdk.TransferClient.submit_transfer>`.

    At least one item must be added using
    :meth:`add_item <globus_sdk.TransferData.add_item>`.

    If ``submission_id`` isn't passed, one will be fetched automatically. The
    submission ID can be pulled out of here to inspect, but the document
    can be used as-is multiple times over to retry a potential submission
    failure (so there shouldn't be any need to inspect it).

    :param transfer_client: A ``TransferClient`` instance which will be used to get a
        submission ID if one is not supplied. Should be the same instance that is used
        to submit the transfer.
    :type transfer_client: :class:`TransferClient <globus_sdk.TransferClient>`
    :param source_endpoint: The endpoint ID of the source endpoint
    :type source_endpoint: str
    :param destination_endpoint: The endpoint ID of the destination endpoint
    :type destination_endpoint: str
    :param label: A string label for the Task
    :type label: str, optional
    :param submission_id: A submission ID value fetched via :meth:`get_submission_id \
        <globus_sdk.TransferClient.get_submission_id>`. Defaults to using
        ``transfer_client.get_submission_id``
    :type submission_id: str, optional
    :param sync_level: The method used to compare items between the source and
        destination. One of  ``"exists"``, ``"size"``, ``"mtime"``, or ``"checksum"``
        See the section below on sync-level for an explanation of values.
    :type sync_level: int or str, optional
    :param verify_checksum: When true, after transfer verify that the source and
        destination file checksums match. If they don't, re-transfer the entire file and
        keep trying until it succeeds. This will create CPU load on both the origin and
        destination of the transfer, and may even be a bottleneck if the network speed
        is high enough.
        [default: ``False``]
    :type verify_checksum: bool, optional
    :param preserve_timestamp: When true, Globus Transfer will attempt to set file
        timestamps on the destination to match those on the origin. [default: ``False``]
    :type preserve_timestamp: bool, optional
    :param encrypt_data: When true, all files will be TLS-protected during transfer.
        [default: ``False``]
    :type encrypt_data: bool, optional
    :param deadline: An ISO-8601 timestamp (as a string) or a datetime object which
        defines a deadline for the transfer. At the deadline, even if the data transfer
        is not complete, the job will be canceled. We recommend ensuring that the
        timestamp is in UTC to avoid confusion and ambiguity. Examples of ISO-8601
        timestamps include ``2017-10-12 09:30Z``, ``2017-10-12 12:33:54+00:00``, and
        ``2017-10-12``
    :type deadline: str or datetime, optional
    :param recursive_symlinks: Specify the behavior of recursive directory transfers
        when encountering symlinks. One of ``"ignore"``, ``"keep"``, or ``"copy"``.
        ``"ignore"`` skips symlinks, ``"keep"`` creates symlinks at the destination
        matching the source (without modifying the link path at all), and
        ``"copy"`` follows symlinks on the source, failing if the link is invalid.
        [default: ``"ignore"``]
    :type recursive_symlinks: str
    :param skip_source_errors: When true, source permission denied and file
        not found errors from the source endpoint will cause the offending
        path to be skipped.
        [default: ``False``]
    :type skip_source_errors: bool, optional
    :param fail_on_quota_errors: When true, quota exceeded errors will cause the
        task to fail.
        [default: ``False``]
    :type fail_on_quota_errors: bool, optional

    Any additional parameters are fed into the dict being created verbatim.

    **Sync Levels**

    The values for ``sync_level`` are used to determine how comparisons are made between
    files found both on the source and the destination. When files match, no data
    transfer will occur.

    For compatibility, this can be an integer ``0``, ``1``, ``2``, or ``3`` in addition
    to the string values.

    The meanings are as follows:

    =====================   ========
    value                   behavior
    =====================   ========
    ``0``, ``exists``       Determine whether or not to transfer based on file
                            existence. If the destination file is absent, do the
                            transfer.
    ``1``, ``size``         Determine whether or not to transfer based on the size of
                            the file. If destination file size does not match the
                            source, do the transfer.
    ``2``, ``mtime``        Determine whether or not to transfer based on modification
                            times. If source has a newer modififed time than the
                            destination, do the transfer.
    ``3``, ``checksum``     Determine whether or not to transfer based on checksums of
                            file contents. If source and destination contents differ, as
                            determined by a checksum of their contents, do the transfer.
    =====================   ========

    **Examples**

    See the
    :meth:`submit_transfer <globus_sdk.TransferClient.submit_transfer>`
    documentation for example usage.

    **External Documentation**

    See the
    `Task document definition \
    <https://docs.globus.org/api/transfer/task_submit/#document_types>`_
    and
    `Transfer specific fields \
    <https://docs.globus.org/api/transfer/task_submit/#transfer_specific_fields>`_
    in the REST documentation for more details on Transfer Task documents.

    .. automethodlist:: globus_sdk.TransferData
    """

    def __init__(
        self,
        transfer_client,
        source_endpoint,
        destination_endpoint,
        label=None,
        submission_id=None,
        sync_level=None,
        verify_checksum=False,
        preserve_timestamp=False,
        encrypt_data=False,
        deadline=None,
        skip_source_errors=False,
        fail_on_quota_errors=False,
        recursive_symlinks="ignore",
        **kwargs,
    ):
        source_endpoint = safe_stringify(source_endpoint)
        destination_endpoint = safe_stringify(destination_endpoint)
        logger.info("Creating a new TransferData object")
        self["DATA_TYPE"] = "transfer"
        self["submission_id"] = (
            submission_id or transfer_client.get_submission_id()["value"]
        )
        logger.info("TransferData.submission_id = {}".format(self["submission_id"]))
        self["source_endpoint"] = source_endpoint
        logger.info(f"TransferData.source_endpoint = {source_endpoint}")
        self["destination_endpoint"] = destination_endpoint
        logger.info(f"TransferData.destination_endpoint = {destination_endpoint}")
        self["verify_checksum"] = verify_checksum
        logger.info(f"TransferData.verify_checksum = {verify_checksum}")
        self["preserve_timestamp"] = preserve_timestamp
        logger.info(f"TransferData.preserve_timestamp = {preserve_timestamp}")
        self["encrypt_data"] = encrypt_data
        logger.info(f"TransferData.encrypt_data = {encrypt_data}")
        self["recursive_symlinks"] = recursive_symlinks
        logger.info(f"TransferData.recursive_symlinks = {recursive_symlinks}")
        self["skip_source_errors"] = skip_source_errors
        logger.info(f"TransferData.skip_source_errors = {skip_source_errors}")
        self["fail_on_quota_errors"] = fail_on_quota_errors
        logger.info(f"TransferData.fail_on_quota_errors = {fail_on_quota_errors}")

        if label is not None:
            self["label"] = label
            logger.debug(f"TransferData.label = {label}")

        if deadline is not None:
            self["deadline"] = str(deadline)
            logger.debug(f"TransferData.deadline = {deadline}")

        # map the sync_level (if it's a nice string) to one of the known int
        # values
        # you can get away with specifying an invalid sync level -- the API
        # will just reject you with an error. This is kind of important: if
        # more levels are added in the future this method doesn't become
        # garbage overnight
        if sync_level is not None:
            sync_dict = {"exists": 0, "size": 1, "mtime": 2, "checksum": 3}
            self["sync_level"] = sync_dict.get(sync_level, sync_level)
            logger.info(
                "TransferData.sync_level = {} ({})".format(
                    self["sync_level"], sync_level
                )
            )

        self["DATA"] = []

        self.update(kwargs)
        for option, value in kwargs.items():
            logger.info(
                "TransferData.{} = {} (option passed in via kwargs)".format(
                    option, value
                )
            )

    def add_item(
        self,
        source_path,
        destination_path,
        recursive=False,
        external_checksum=None,
        checksum_algorithm=None,
        **params,
    ):
        """
        Add a file or directory to be transfered. If the item is a symlink
        to a file or directory, the file or directory at the target of
        the symlink will be transfered.

        Appends a transfer_item document to the DATA key of the transfer
        document.

        .. note::

            The full path to the destination file must be provided for file items.
            Parent directories of files are not allowed. See
            `task submission documentation
            <https://docs.globus.org/api/transfer/task_submit/#submit_transfer_task>`_
            for more details.

        :param source_path: Path to the source directory or file to be transfered
        :type source_path: str
        :param destination_path: Path to the source directory or file will be
            transfered to
        :type destination_path: str
        :param recursive: Set to True if the target at source path is a directory
        :type recursive: bool
        :param external_checksum: A checksum to verify both source file and destination
            file integrity. The checksum will be verified after the data transfer and a
            failure will cause the entire task to fail. Cannot be used with directories.
            Assumed to be an MD5 checksum unless checksum_algorithm is also given.
        :type external_checksum: str, optional
        :param checksum_algorithm: Specifies the checksum algorithm to be used when
            verify_checksum is True, sync_level is "checksum" or 3, or an
            external_checksum is given.
        :type checksum_algorithm: str, optional
        """
        source_path = safe_stringify(source_path)
        destination_path = safe_stringify(destination_path)
        item_data = {
            "DATA_TYPE": "transfer_item",
            "source_path": source_path,
            "destination_path": destination_path,
            "recursive": recursive,
            "external_checksum": external_checksum,
            "checksum_algorithm": checksum_algorithm,
        }
        item_data.update(params)

        logger.debug(
            'TransferData[{}, {}].add_item: "{}"->"{}"'.format(
                self["source_endpoint"],
                self["destination_endpoint"],
                source_path,
                destination_path,
            )
        )
        self["DATA"].append(item_data)

    def add_symlink_item(self, source_path, destination_path):
        """
        Add a symlink to be transfered as a symlink rather than as the
        target of the symlink.

        Appends a transfer_symlink_item document to the DATA key of the
        transfer document.

        :param source_path: Path to the source symlink
        :type source_path: str
        :param destination_path: Path to which the source symlink will be transfered
        :type destination_path: str
        """
        source_path = safe_stringify(source_path)
        destination_path = safe_stringify(destination_path)
        item_data = {
            "DATA_TYPE": "transfer_symlink_item",
            "source_path": source_path,
            "destination_path": destination_path,
        }
        logger.debug(
            'TransferData[{}, {}].add_symlink_item: "{}"->"{}"'.format(
                self["source_endpoint"],
                self["destination_endpoint"],
                source_path,
                destination_path,
            )
        )
        self["DATA"].append(item_data)


class DeleteData(dict):
    r"""
    Convenience class for constructing a delete document, to use as the
    `data` parameter to
    :meth:`submit_delete <globus_sdk.TransferClient.submit_delete>`.

    At least one item must be added using
    :meth:`add_item <globus_sdk.DeleteData.add_item>`.

    If ``submission_id`` isn't passed, one will be fetched automatically. The
    submission ID can be pulled out of here to inspect, but the document
    can be used as-is multiple times over to retry a potential submission
    failure (so there shouldn't be any need to inspect it).

    :param transfer_client: A ``TransferClient`` instance which will be used to get a
        submission ID if one is not supplied. Should be the same instance that is used
        to submit the deletion.
    :type transfer_client: :class:`TransferClient <globus_sdk.TransferClient>`
    :param endpoint: The endpoint ID which is targeted by this deletion Task
    :type endpoint: str
    :param label: A string label for the Task
    :type label: str, optional
    :param submission_id: A submission ID value fetched via
        :meth:`get_submission_id <globus_sdk.TransferClient.get_submission_id>`.
        Defaults to using ``transfer_client.get_submission_id``
    :type submission_id: str, optional
    :param recursive: Recursively delete subdirectories on the target endpoint
      [default: ``False``]
    :type recursive: bool
    :param deadline: An ISO-8601 timestamp (as a string) or a datetime object which
        defines a deadline for the deletion. At the deadline, even if the data deletion
        is not complete, the job will be canceled. We recommend ensuring that the
        timestamp is in UTC to avoid confusion and ambiguity. Examples of ISO-8601
        timestamps include ``2017-10-12 09:30Z``, ``2017-10-12 12:33:54+00:00``, and
        ``2017-10-12``
    :type deadline: str or datetime, optional

    **Examples**

    See the :meth:`submit_delete <globus_sdk.TransferClient.submit_delete>`
    documentation for example usage.

    **External Documentation**

    See the
    `Task document definition \
    <https://docs.globus.org/api/transfer/task_submit/#document_types>`_
    and
    `Delete specific fields \
    <https://docs.globus.org/api/transfer/task_submit/#delete_specific_fields>`_
    in the REST documentation for more details on Delete Task documents.

    .. automethodlist:: globus_sdk.TransferData
    """

    def __init__(
        self,
        transfer_client,
        endpoint,
        label=None,
        submission_id=None,
        recursive=False,
        deadline=None,
        **kwargs,
    ):
        endpoint = safe_stringify(endpoint)
        logger.info("Creating a new DeleteData object")
        self["DATA_TYPE"] = "delete"
        self["submission_id"] = (
            submission_id or transfer_client.get_submission_id()["value"]
        )
        logger.info("DeleteData.submission_id = {}".format(self["submission_id"]))
        self["endpoint"] = endpoint
        logger.info(f"DeleteData.endpoint = {endpoint}")
        self["recursive"] = recursive
        logger.info(f"DeleteData.recursive = {recursive}")

        if label is not None:
            self["label"] = label
            logger.debug(f"DeleteData.label = {label}")

        if deadline is not None:
            self["deadline"] = str(deadline)
            logger.debug(f"DeleteData.deadline = {deadline}")

        self["DATA"] = []

        self.update(kwargs)
        for option, value in kwargs.items():
            logger.info(f"DeleteData.{option} = {value} (option passed in via kwargs)")

    def add_item(self, path, **params):
        """
        Add a file or directory or symlink to be deleted. If any of the paths
        are directories, ``recursive`` must be set True on the top level
        ``DeleteData``. Symlinks will never be followed, only deleted.

        Appends a delete_item document to the DATA key of the delete
        document.
        """
        path = safe_stringify(path)
        item_data = {"DATA_TYPE": "delete_item", "path": path}
        item_data.update(params)
        logger.debug('DeleteData[{}].add_item: "{}"'.format(self["endpoint"], path))
        self["DATA"].append(item_data)
