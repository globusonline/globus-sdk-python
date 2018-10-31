import os
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

import pytest
import six
from six.moves.configparser import ConfigParser

import globus_sdk.config

try:
    import mock
except ImportError:
    from unittest import mock


@contextmanager
def custom_config(configdata):
    """
    patch config with a file-like object or even a raw string (which will
    get wrapped in a StringIO to be file-like)

    test helper
    """

    # clear any existing parser
    globus_sdk.config._parser = None

    # not file-like, wrap it
    if not hasattr(configdata, "read"):
        configdata = six.StringIO(configdata)

    def loadconf(cfgparser):
        # try to use the new version of this method, added in py3.2
        try:
            readfp_func = cfgparser._parser.read_file
        # but failover to the pre-3.2 version
        except AttributeError:
            readfp_func = cfgparser._parser.readfp
        # and fail-open if there's some other issue

        readfp_func(configdata)

    with mock.patch("globus_sdk.config.GlobusConfigParser._load_config", loadconf):
        globus_sdk.config._get_parser()
        yield

    # clear that temporary parser
    globus_sdk.config._parser = None


@contextmanager
def only_lib_config():
    """
    patch config to only load library data, ignores /etc/ and ~
    """
    # clear any existing parser
    globus_sdk.config._parser = None

    def loadconf(cfgparser):
        cfgparser._parser.read([globus_sdk.config._get_lib_config_path()])

    with mock.patch("globus_sdk.config.GlobusConfigParser._load_config", loadconf):
        yield

    # clear that temporary parser
    globus_sdk.config._parser = None


def test_get_lib_config():
    """Test lib config file exists, is minimally well formed"""
    path = globus_sdk.config._get_lib_config_path()

    # name is "about right"
    file_name = "globus.cfg"
    assert path.endswith(file_name)

    # ensure that it parses using configparser
    parser = ConfigParser()
    parser.read(path)

    # and check that 'default' and 'preview' are populated
    for env in ("default", "preview"):
        section = "environment {}".format(env)
        for key in (
            "auth_service",
            "nexus_service",
            "transfer_service",
            "search_service",
        ):
            opt = parser.get(section, key)
            assert opt


def test_verify_ssl_true():
    with custom_config("[environment default]\nssl_verify = true\n"):
        assert globus_sdk.config.get_ssl_verify("default")


def test_verify_ssl_false():
    with custom_config("[environment default]\nssl_verify = false\n"):
        assert not globus_sdk.config.get_ssl_verify("default")


def test_verify_ssl_invalid():
    with pytest.raises(ValueError):
        with custom_config("[environment default]\nssl_verify = invalidvalue\n"):
            assert not globus_sdk.config.get_ssl_verify("default")


def test_init_loads():
    """
    ensure that initializing a config parser loads config
    """
    with only_lib_config():
        conf = globus_sdk.config._get_parser()
        assert conf._parser.items("general") is not None


def test_conf_get():
    """
    Confirms that get reads expected results
    Tests section, environment, failover_to_general, and check_env params
    """
    confio = six.StringIO(
        """\
[general]
option = general_value

[section]
option = section_value

[environment section]
option = environment_value

[nonexistent]
"""
    )
    with custom_config(confio):
        conf = globus_sdk.config._get_parser()
        with mock.patch.dict(os.environ):
            os.environ["GLOBUS_SDK_OPTION"] = "os_environ_value"
            assert conf.get("option") == "general_value"
            assert conf.get("option", section="section") == "section_value"
            assert conf.get("option", environment="section") == "environment_value"
            assert conf.get("option", section="nonexistent") is None
            assert (
                conf.get("option", section="nonexistent", failover_to_general=True)
                == "general_value"
            )
            assert conf.get("option", check_env=True) == "os_environ_value"
            # environment > section
            assert (
                conf.get("option", section="section", environment="section")
                == "environment_value"
            )
            # check_env > environment
            assert (
                conf.get("option", environment="section", check_env=True)
                == "os_environ_value"
            )


def test_parser_is_singleton():
    # do two fetches, assert 'is'
    assert globus_sdk.config._get_parser() is globus_sdk.config._get_parser()


def test_get_service_url():
    """
    Confirms get_service_url returns expected results
    Tests environments, services, and missing values
    """
    confio = six.StringIO(
        """\
[general]

[environment default]
auth_service = https://auth.globus.org/
transfer_service = https://transfer.api.globus.org/

[environment preview]
auth_service = https://auth.preview.globus.org/
transfer_service = https://transfer.api.preview.globus.org/

[environment nonexistent]
"""
    )
    with custom_config(confio):
        assert (
            globus_sdk.config.get_service_url("default", "auth")
            == "https://auth.globus.org/"
        )
        assert (
            globus_sdk.config.get_service_url("default", "transfer")
            == "https://transfer.api.globus.org/"
        )
        assert (
            globus_sdk.config.get_service_url("preview", "auth")
            == "https://auth.preview.globus.org/"
        )
        assert (
            globus_sdk.config.get_service_url("preview", "transfer")
            == "https://transfer.api.preview.globus.org/"
        )

        with pytest.raises(ValueError):
            globus_sdk.config.get_service_url("nonexistent", "auth")


def test_get_ssl_verify():
    """
    Confirms get_ssl_verify returns expected results
    Tests true/false, and invalid values
    """
    confio = six.StringIO(
        """\
[general]

[environment trueenv]
ssl_verify = true

[environment falseenv]
ssl_verify = false

[environment invalid]
ssl_verify = invalid

[environment nonexistent]
"""
    )
    with custom_config(confio):
        assert globus_sdk.config.get_ssl_verify("trueenv")
        assert not globus_sdk.config.get_ssl_verify("falseenv")
        # default = True
        assert globus_sdk.config.get_ssl_verify("nonexistent")

        with pytest.raises(ValueError):
            globus_sdk.config.get_ssl_verify("invalid")


@pytest.mark.parametrize(
    "value, expected_result",
    [(x, True) for x in [str(True), "1", "YES", "true", "True", "ON"]]
    + [(x, False) for x in [str(False), "0", "NO", "false", "False", "OFF"]]
    + [(x, ValueError) for x in ["invalid", "1.0", "0.0", "t", "f"]],
)
def test_bool_cast(value, expected_result):
    """
    Confirms bool cast returns correct bools from sets of string values
    """
    if isinstance(expected_result, bool):
        assert globus_sdk.config._bool_cast(value) == expected_result
    else:
        with pytest.raises(expected_result):
            globus_sdk.config._bool_cast(value)


def test_get_globus_environ():
    with mock.patch.dict(os.environ):
        # set an environment value, ensure that it's returned
        os.environ["GLOBUS_SDK_ENVIRONMENT"] = "beta"
        assert globus_sdk.config.get_globus_environ() == "beta"

        # clear that value, "default" should be returned
        del os.environ["GLOBUS_SDK_ENVIRONMENT"]
        assert globus_sdk.config.get_globus_environ() == "default"

        # ensure that passing a value returns that value
        assert globus_sdk.config.get_globus_environ("beta") == "beta"


def test_get_globus_environ_production():
    """
    Confirms that get_globus_environ translates "production" to "default",
    including when special values are passed
    """
    # mock environ to ensure it gets reset
    with mock.patch.dict(os.environ):
        os.environ["GLOBUS_SDK_ENVIRONMENT"] = "production"
        assert globus_sdk.config.get_globus_environ() == "default"

        del os.environ["GLOBUS_SDK_ENVIRONMENT"]
        # ensure that passing a value returns that value
        assert globus_sdk.config.get_globus_environ("production") == "default"


def test_verify_set_config_file():
    new_config = NamedTemporaryFile()
    with custom_config(""):
        cfg = globus_sdk.config.get_parser()
        cfg.set_write_config_file(new_config.name)
        assert cfg._write_path == new_config.name


def test_verify_load_from_new_config_file():
    with custom_config(""), NamedTemporaryFile(mode="w+") as new_cfg:
        new_cfg.file.write("[default]\noption = general_value\n")
        new_cfg.file.flush()

        cfg = globus_sdk.config.get_parser()
        cfg.set_write_config_file(new_cfg.name)
        assert cfg.get("option", "default") == "general_value"


def test_verify_write_config_option(temp_config):
    with custom_config(""):
        temp_config.set("foo", "bar", "mysec")
        assert temp_config.get("foo", "mysec") == "bar"

        temp_config.set("baz", "car", "new_sec")
        assert temp_config.get("baz", "new_sec") == "car"


def test_verify_remove_config_option(temp_config):
    with custom_config(""):
        temp_config.set("foo", "bar", "mysec")
        assert temp_config.get("foo", "mysec") == "bar"
        temp_config.remove("foo", "mysec")
        assert temp_config.get("foo", "mysec") is None
