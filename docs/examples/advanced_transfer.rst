Advanced Transfer Client Usage
------------------------------

This is a collection of examples of advanced usage patterns leveraging the
:class:`TransferClient <globus_sdk.TransferClient>`.


Relative Task Deadlines
~~~~~~~~~~~~~~~~~~~~~~~

One of the lesser-known features of the Globus Transfer service is the ability
for users to set a ``deadline`` by which a Transfer or Delete task must
complete. If the task is still in progress when the ``deadline`` is reached,
it is aborted.

You can use this, for example, to enforce that a Transfer Task which takes too
long results in errors (even if it is making slow progress).

Because the ``deadline`` is accepted as an ISO 8601 date, you can use python's
built-in ``datetime`` library to compute a timestamp to pass to the service.

Start out by computing the current time as a ``datetime``:

.. code-block:: python

    import datetime
    now = datetime.datetime.utcnow()

Then, compute a relative timestamp using ``timedelta``:

.. code-block:: python

    future_1minute = now + datetime.timedelta(minutes=1)

This value can be passed to a :class:`TransferData <globus_sdk.TransferData>`,
as in

.. code-block:: python

    import globus_sdk
    # get various components needed for a Transfer Task
    # beyond the scope of this example
    transfer_client = globus_sdk.TransferClient(...)
    source_endpoint_uuid = ...
    dest_endpoint_uuid = ...

    # note how `future_1minute` is used here
    submission_data = globus_sdk.TransferData(
        transfer_client, source_endpoint_uuid, dest_endpoint_uuid,
        deadline=str(future_1minute))


Retrying Task Submission
~~~~~~~~~~~~~~~~~~~~~~~~

Globus Transfer and Delete Tasks are often scheduled and submitted by
automated systems and scripts. In these scenarios, it's often desirable to
retry submission in the event of network or service errors to ensure that the
job is really submitted.

There are two key pieces to doing this correctly: Once and Only Once
Submission, and logging captured errors.

For once-and-only-once task submission, you can explicitly invoke
:meth:`TransferClient.get_submission_id()
<globus_sdk.TransferClient.get_submission_id>`, which is a unique ID used to
ensure exactly this. However, :class:`TransferData <globus_sdk.TransferData>` and
:class:`DeleteData <globus_sdk.DeleteData>` both implicitly invoke this method if they
are initialized without an explicit ``submission_id``.

For proper logging, we'll rely on the standard library ``logging`` package.

In this example, we'll retry task submission 5 times, and we'll want to separate
retry logic from the core task submission logic.

.. code-block:: python

    import logging
    from globus_sdk import GlobusAPIError, NetworkError

    # putting logger objects named by the module name into the module-level
    # scope is a common best practice -- for more details, you should look
    # into the python logging documentation
    logger = logging.getLogger(__name__)


    def retry_globus_function(func, retries=5, func_name='<func>'):
        """
        Define what it means to retry a "Globus Function", some function or
        method which produces Globus SDK errors on failure.
        """
        def actually_retry():
            """
            Helper: run the next retry
            """
            return retry_globus_function(func, retries=(retries - 1),
                                         func_name=func_name)

        def check_for_reraise():
            """
            Helper: check if we should reraise an error
                    logs an error message on reraise
                    must be run inside an exception handler
            """
            if retries < 1:
                logger.error('Retried {0} too many times.'
                             .format(func_name))
                raise

        try:
            return func()
        except NetworkError:
            # log with exc_info=True to capture a full stacktrace as a
            # debug-level log
            logger.debug(('Globus func {0} experienced a network error'
                          .format(func_name)), exc_info=True)
            check_for_reraise()
        except GlobusAPIError:
            # again, log with exc_info=True to capture a full stacktrace
            logger.warn(('Globus func {0} experienced a network error'
                         .format(func_name)), exc_info=True)
            check_for_reraise()

        # if we reach this point without returning or erroring, retry
        return actually_retry()


The above is a fairly generic tool for retrying any function which throws
``globus_sdk.NetworkError`` and ``globus_sdk.GlobusAPIError`` errors. It is not
even specific to task resubmission, so you could use it against other
retry-safe Globus APIs.

Now, moving on to creating a retry-safe function to put into it, things get a
little bit tricky. The retry handler above requires a function which takes no
arguments, so we'll have to define a function dynamically which fits that
constraint:

.. code-block:: python

    def submit_transfer_with_retries(transfer_client, transfer_data):
        # create a function with no arguments, for our retry handler
        def locally_bound_func():
            return transfer_client.submit_transfer(transfer_data)
        return retry_globus_function(locally_bound_func,
                                     func_name='submit_transfer')

Now we're finally all-set to create a ``TransferData`` and submit it:

.. code-block:: python

    from globus_sdk import TransferClient, TransferData
    # get various components needed for a Transfer Task
    # beyond the scope of this example
    transfer_client = TransferClient(...)
    source_endpoint_uuid = ...
    dest_endpoint_uuid = ...

    submission_data = TransferData(
        transfer_client, source_endpoint_uuid, dest_endpoint_uuid)

    # add any number of items to the submission data
    submission_data.add_item('/source/path', 'dest/path')
    ...

    # do it!
    submit_transfer_with_retries(transfer_client, submission_data)

The same exact approach can be applied to ``TransferClient.submit_delete``, and
a wide variety of other SDK methods.
