"""Exhaustive tests for config_manager.config."""

import pytest
from config_manager import ConfigFrozenError, ConfigKeyError, Field, Schema, load
from config_manager.config import FrozenConfig, _freeze_nested, _thaw_nested
from config_manager.errors import ConfigError


def test_frozen_config_mapping(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    assert len(config) > 0
    assert "app" in config
    assert config["app"]["name"] == "Demo"


def test_frozen_config_attribute_access(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    assert config.app.name == "Demo"


def test_frozen_config_missing_attribute():
    config = load(Schema({"a": Field(str, default="x")}))
    with pytest.raises(AttributeError):
        _ = config.missing  # noqa: B018


def test_config_get_default(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    assert config.get("app.debug") is False


def test_config_get_missing_raises(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    with pytest.raises(ConfigKeyError):
        config.get("missing.path")


def test_config_get_with_default(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    assert config.get("missing", "fallback") == "fallback"


def test_config_explain_set(basic_schema):
    config = load(
        basic_schema,
        cli_overrides={"app.name": "Demo", "database.password": "pw", "app.port": "9090"},
    )
    info = config.explain("app.port")
    assert info["status"] == "set"
    assert info["source"] == "cli"
    assert info["type"] == "int"


def test_config_explain_not_set():
    schema = Schema({"opt": Field(str)})
    config = load(schema)
    info = config.explain("opt")
    assert info["status"] == "not_set"


def test_config_explain_not_in_schema(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    with pytest.raises(ConfigError, match="not declared"):
        config.explain("bogus.path")


def test_config_provenance(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    prov = config.provenance("app.name")
    assert prov is not None
    assert prov.source == "cli"


def test_config_to_dict_roundtrip(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    d = config.to_dict()
    assert isinstance(d, dict)
    assert d["app"]["name"] == "Demo"


def test_config_to_masked_dict(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "secret"})
    masked = config.to_masked_dict()
    assert masked["database"]["password"] == "********"


def test_config_immutable_assignment(basic_schema):
    config = load(basic_schema, cli_overrides={"app.name": "Demo", "database.password": "pw"})
    with pytest.raises(ConfigFrozenError):
        config.app = "other"  # type: ignore[misc]


def test_list_frozen_as_tuple():
    schema = Schema({"tags": Field(list, default=[], item_type=str)})
    config = load(schema, env={"MYAPP_TAGS": "a,b"}, prefix="MYAPP")
    tags = config.get("tags")
    assert isinstance(tags, tuple)


def test_freeze_nested_dict():
    frozen = _freeze_nested({"a": {"b": 1}, "c": [1, 2]})
    assert isinstance(frozen["a"], FrozenConfig)
    assert frozen["c"] == (1, 2)


def test_thaw_nested():
    inner = _freeze_nested({"x": 1})
    assert _thaw_nested(inner) == {"x": 1}
