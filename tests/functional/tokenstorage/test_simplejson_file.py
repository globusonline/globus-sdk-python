import json
import os

import pytest

from globus_sdk.tokenstorage import SimpleJSONFileAdapter
from globus_sdk.version import __version__

IS_WINDOWS = os.name == "nt"


@pytest.fixture
def filename(tempdir):
    return os.path.join(tempdir, "mydata.json")


@pytest.mark.parametrize(
    "success, kwargs",
    [
        (False, {}),
        (False, {"resource_server": "foo", "scopes": ["bar"]}),
        (True, {"resource_server": "foo"}),
        (True, {"scopes": ["bar"]}),
    ],
)
def test_constructor(filename, success, kwargs):
    if success:
        assert SimpleJSONFileAdapter(filename, **kwargs)
    else:
        with pytest.raises(ValueError):
            SimpleJSONFileAdapter(filename, **kwargs)


def test_file_dne(filename):
    adapter = SimpleJSONFileAdapter(filename, scopes=["x"])
    assert not adapter.file_exists()


def test_file_exists(filename):
    open(filename, "w").close()  # open and close to touch
    adapter = SimpleJSONFileAdapter(filename, scopes=["x"])
    assert adapter.file_exists()


def test_read_as_dict(filename):
    with open(filename, "w") as f:
        json.dump({"x": 1}, f)
    adapter = SimpleJSONFileAdapter(filename, scopes=["x"])
    assert adapter.file_exists()

    d = adapter.read_as_dict()

    assert d == {"x": 1}


def test_store(filename, mock_response):
    adapter = SimpleJSONFileAdapter(filename, resource_server="resource_server_1")
    assert not adapter.file_exists()
    adapter.store(mock_response)

    with open(filename) as f:
        data = json.load(f)
    assert data["globus-sdk.version"] == __version__
    assert data["access_token"] == "access_token_1"


@pytest.mark.xfail(IS_WINDOWS, reason="cannot set umask perms on Windows")
def test_store_perms(filename, mock_response):
    adapter = SimpleJSONFileAdapter(filename, resource_server="resource_server_1")
    assert not adapter.file_exists()
    adapter.store(mock_response)

    # mode|0600 should be 0600 -- meaning that those are the maximal
    # permissions given
    st_mode = os.stat(filename).st_mode & 0o777  # & 777 to remove extra bits
    assert st_mode | 0o600 == 0o600
