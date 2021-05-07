import os

import pytest

from globus_sdk.tokenstorage import SQLiteAdapter


@pytest.fixture
def db_filename(tempdir):
    return os.path.join(tempdir, "test.db")


MEMORY_DBNAME = ":memory:"


@pytest.mark.parametrize(
    "success, use_file, kwargs",
    [
        (False, False, {}),
        (False, False, {"namespace": "foo"}),
        (True, False, {"dbname": MEMORY_DBNAME}),
        (True, False, {"dbname": MEMORY_DBNAME, "namespace": "foo"}),
        (True, True, {}),
        (True, True, {"namespace": "foo"}),
        (False, True, {"dbname": MEMORY_DBNAME}),
        (False, True, {"dbname": MEMORY_DBNAME, "namespace": "foo"}),
    ],
)
def test_constructor(success, use_file, kwargs, db_filename):
    if success:
        if use_file:
            assert SQLiteAdapter(db_filename, **kwargs)
        else:
            assert SQLiteAdapter(**kwargs)
    else:
        with pytest.raises(TypeError):
            if use_file:
                SQLiteAdapter(db_filename, **kwargs)
            else:
                SQLiteAdapter(**kwargs)


def test_store_and_retrieve_simple_config():
    adapter = SQLiteAdapter(MEMORY_DBNAME)
    store_val = {"val1": True, "val2": None, "val3": 1.4}
    adapter.store_config("myconf", store_val)
    read_val = adapter.read_config("myconf")
    assert read_val == store_val
    assert read_val is not store_val


def test_store_and_retrieve(mock_response):
    adapter = SQLiteAdapter(MEMORY_DBNAME)
    adapter.store(mock_response)

    data = adapter.get_by_resource_server()
    assert data == mock_response.by_resource_server


def test_on_refresh_and_retrieve(mock_response):
    """just confirm that the aliasing of these functions does not change anything"""
    adapter = SQLiteAdapter(MEMORY_DBNAME)
    adapter.on_refresh(mock_response)

    data = adapter.get_by_resource_server()
    assert data == mock_response.by_resource_server


def test_multiple_adapters_store_and_retrieve(mock_response, db_filename):
    adapter1 = SQLiteAdapter(db_filename)
    adapter2 = SQLiteAdapter(db_filename)
    adapter1.store(mock_response)

    data = adapter2.get_by_resource_server()
    assert data == mock_response.by_resource_server


def test_multiple_adapters_store_and_retrieve_different_namespaces(
    mock_response, db_filename
):
    adapter1 = SQLiteAdapter(db_filename, namespace="foo")
    adapter2 = SQLiteAdapter(db_filename, namespace="bar")
    adapter1.store(mock_response)

    data = adapter2.get_by_resource_server()
    assert data == {}


def test_load_missing_config_data():
    adapter = SQLiteAdapter(MEMORY_DBNAME)
    assert adapter.read_config("foo") is None


def test_load_missing_token_data():
    adapter = SQLiteAdapter(MEMORY_DBNAME)
    assert adapter.get_by_resource_server() == {}
    assert adapter.get_token_data("resource_server_1") is None


def test_remove_tokens(mock_response):
    adapter = SQLiteAdapter(MEMORY_DBNAME)
    adapter.store(mock_response)

    removed = adapter.remove_tokens_for_resource_server("resource_server_1")
    assert removed
    data = adapter.get_by_resource_server()
    assert data == {
        "resource_server_2": mock_response.by_resource_server["resource_server_2"]
    }

    removed = adapter.remove_tokens_for_resource_server("resource_server_1")
    assert not removed


def test_remove_config():
    adapter = SQLiteAdapter(MEMORY_DBNAME)
    store_val = {"val1": True, "val2": None, "val3": 1.4}
    adapter.store_config("myconf", store_val)
    adapter.store_config("myconf2", store_val)
    removed = adapter.remove_config("myconf")
    assert removed
    read_val = adapter.read_config("myconf")
    assert read_val is None
    read_val = adapter.read_config("myconf2")
    assert read_val == store_val

    removed = adapter.remove_config("myconf")
    assert not removed


def test_store_and_refresh(mock_response, mock_refresh_response):
    adapter = SQLiteAdapter(MEMORY_DBNAME)
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
