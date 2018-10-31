import tempfile

import pytest

import globus_sdk


@pytest.yield_fixture
def temp_config():
    globus_sdk.config._parser = None
    temp_config = tempfile.NamedTemporaryFile()
    cfg = globus_sdk.config.get_parser()
    cfg.set_write_config_file(temp_config.name)
    yield cfg
    temp_config.close()
