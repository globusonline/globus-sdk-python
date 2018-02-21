import unittest
import subprocess
import os


PYTHON_BINARY = os.environ.get('GLOBUS_TEST_PY', 'python')


class TestImports(unittest.TestCase):
    """
    Various tests for imports from the SDK to ensure that our `__all__`
    declarations are correct and complete.

    To ensure that we aren't contaminating these tests with the current
    interpreter's state, invoke these via subprocess check_call() calls.
    These should all be using `shell=True` (the subprocess invoked interpreter
    doesn't behave correclty without it).
    """

    def _check_import_str(self, s):
        proc = subprocess.Popen('{0} -c "{1}"'.format(PYTHON_BINARY, s),
                                shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        status = proc.wait()
        assert status is 0, str(proc.communicate())

    def test_import_splat(self):
        self._check_import_str("from globus_sdk import *")

    def test_import_clients(self):
        self._check_import_str(
            "from globus_sdk import TransferClient, AuthClient")
