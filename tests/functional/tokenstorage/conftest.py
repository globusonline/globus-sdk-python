import shutil
import tempfile
import time
from unittest import mock

import pytest


@pytest.fixture
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


@pytest.fixture
def mock_response():
    res = mock.Mock()
    expiration_time = int(time.time()) + 3600
    res.by_resource_server = {
        "resource_server_1": {
            "access_token": "access_token_1",
            "expires_at_seconds": expiration_time,
            "refresh_token": "refresh_token_1",
            "resource_server": "resource_server_1",
            "scope": "scope1",
            "token_type": "bearer",
        },
        "resource_server_2": {
            "access_token": "access_token_2",
            "expires_in": expiration_time,
            "refresh_token": "refresh_token_2",
            "resource_server": "resource_server_2",
            "scope": "scope2 scope2:0 scope2:1",
            "token_type": "bearer",
        },
    }
    return res
