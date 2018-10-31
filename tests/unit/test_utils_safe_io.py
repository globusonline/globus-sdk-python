from tempfile import NamedTemporaryFile

from globus_sdk.utils import safeio

try:
    import mock
except ImportError:
    from unittest import mock


def test_safe_print_custom_output():
    my_log_file = NamedTemporaryFile()

    def my_logger(message):
        with open(my_log_file.name, "w+") as lfh:
            lfh.write(message)

    safeio.get_safe_io().set_write_function(my_logger)
    safeio.safe_print("The hamsters are attacking!")
    with open(my_log_file.name) as lfh:
        assert lfh.read() == "The hamsters are attacking!"


def test_safe_print_normally():
    with mock.patch("globus_sdk.utils.safeio._safe_io") as sio:
        safeio.safe_print("foo")
        sio.write.assert_called_once_with("foo")
