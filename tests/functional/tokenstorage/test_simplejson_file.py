import json
import os

import pytest

from globus_sdk.tokenstorage import SimpleJSONFileAdapter
from globus_sdk.version import __version__

IS_WINDOWS = os.name == "nt"


@pytest.fixture
def filename(tempdir):
    return os.path.join(tempdir, "mydata.json")


def test_file_dne(filename):
    adapter = SimpleJSONFileAdapter(filename)
    assert not adapter.file_exists()


def test_file_exists(filename):
    open(filename, "w").close()  # open and close to touch
    adapter = SimpleJSONFileAdapter(filename)
    assert adapter.file_exists()


def test_store(filename, mock_response):
    adapter = SimpleJSONFileAdapter(filename)
    assert not adapter.file_exists()
    adapter.store(mock_response)

    with open(filename) as f:
        data = json.load(f)
    assert data["globus-sdk.version"] == __version__
    assert data["by_rs"]["resource_server_1"]["access_token"] == "access_token_1"
    assert data["by_rs"]["resource_server_2"]["access_token"] == "access_token_2"


def test_get_token_data(filename, mock_response):
    adapter = SimpleJSONFileAdapter(filename)
    assert not adapter.file_exists()
    adapter.store(mock_response)

    data = adapter.get_token_data("resource_server_1")
    assert data["access_token"] == "access_token_1"


def test_store_and_refresh(filename, mock_response, mock_refresh_response):
    adapter = SimpleJSONFileAdapter(filename)
    assert not adapter.file_exists()
    adapter.store(mock_response)

    # rs1 and rs2 data was stored correctly
    data = adapter.get_token_data("resource_server_1")
    assert data["access_token"] == "access_token_1"
    data = adapter.get_token_data("resource_server_2")
    assert data["access_token"] == "access_token_2"

    # "refresh" happens, this should change rs2 but not rs1
    adapter.store(mock_refresh_response)
    data = adapter.get_token_data("resource_server_1")
    assert data["access_token"] == "access_token_1"
    data = adapter.get_token_data("resource_server_2")
    assert data["access_token"] == "access_token_2_refreshed"


@pytest.mark.xfail(IS_WINDOWS, reason="cannot set umask perms on Windows")
def test_store_perms(filename, mock_response):
    adapter = SimpleJSONFileAdapter(filename)
    assert not adapter.file_exists()
    adapter.store(mock_response)

    # mode|0600 should be 0600 -- meaning that those are the maximal
    # permissions given
    st_mode = os.stat(filename).st_mode & 0o777  # & 777 to remove extra bits
    assert st_mode | 0o600 == 0o600
