"""Exhaustive tests for config_manager.sources."""

import pytest
from config_manager import Field, Schema
from config_manager.errors import ConfigError, ParseError
from config_manager.sources import (
    _key_to_dotted,
    _resolve_env_key,
    cli_overrides_source,
    defaults_source,
    dotenv_source,
    environment_source,
    normalize_prefix,
    parse_cli_set,
    toml_source,
)


def test_normalize_prefix_none():
    assert normalize_prefix(None) is None


def test_normalize_prefix_valid():
    assert normalize_prefix("MYAPP") == "MYAPP"


def test_normalize_prefix_empty_raises():
    with pytest.raises(ConfigError):
        normalize_prefix("")


def test_key_to_dotted():
    assert _key_to_dotted("DATABASE__PORT") == "database.port"
    assert _key_to_dotted("APP__NAME") == "app.name"


def test_resolve_env_key_with_prefix():
    result = _resolve_env_key(
        "MYAPP_APP__NAME",
        prefix="MYAPP",
        prefix_text="MYAPP_",
        env_key_map={},
    )
    assert result == ("app.name", "APP__NAME")


def test_resolve_env_key_skips_unprefixed():
    assert _resolve_env_key("OTHER", prefix="MYAPP", prefix_text="MYAPP_", env_key_map={}) is None


def test_resolve_env_key_custom_env_name():
    schema = Schema({"api": {"token": Field(str, env_name="API_TOKEN")}})
    env_map = schema.env_key_map(prefix="MYAPP")
    result = _resolve_env_key(
        "MYAPP_API_TOKEN", prefix="MYAPP", prefix_text="MYAPP_", env_key_map=env_map
    )
    assert result is not None
    assert result[0] == "api.token"


def test_defaults_source(basic_schema):
    data, prov = defaults_source(basic_schema)
    assert data["app"]["debug"] is False
    assert "app.debug" in prov


def test_toml_source_none():
    data, prov = toml_source(None)
    assert data == {} and prov == {}


def test_environment_source_no_prefix():
    data, prov = environment_source({"APP__NAME": "x"}, prefix=None)
    assert data == {}


def test_environment_source_allow_prefixless():
    data, _ = environment_source({"NAME": "x"}, prefix=None, allow_prefixless=True)
    assert data == {"name": "x"}


def test_parse_cli_set_empty():
    assert parse_cli_set(None) == {}
    assert parse_cli_set([]) == {}


def test_parse_cli_set_valid():
    assert parse_cli_set(["a.b=1", "c=2"]) == {"a.b": "1", "c": "2"}


def test_parse_cli_set_no_equals():
    with pytest.raises(ParseError):
        parse_cli_set(["bad"])


def test_parse_cli_set_empty_key():
    with pytest.raises(ParseError):
        parse_cli_set(["=value"])


def test_cli_overrides_invalid_key():
    with pytest.raises(ParseError):
        cli_overrides_source({".bad": "1"})


def test_cli_overrides_cli_name(basic_schema):
    schema = Schema({"db": {"port": Field(int, cli_name="db-port")}})
    data, prov = cli_overrides_source({"db-port": "5432"}, schema=schema)
    assert data["db"]["port"] == "5432"
    assert prov["db.port"].source == "cli"


def test_dotenv_source_skips_unprefixed(tmp_path, basic_schema):
    env_file = tmp_path / ".env"
    env_file.write_text("MYAPP_APP__NAME=ok\nOTHER=bad\n", encoding="utf-8")
    data, _ = dotenv_source(env_file, prefix="MYAPP", schema=basic_schema)
    assert data["app"]["name"] == "ok"
    assert "other" not in data


def test_toml_source_file(tmp_path):
    toml_file = tmp_path / "app.toml"
    toml_file.write_text('[app]\nname = "Demo"\n', encoding="utf-8")
    data, prov = toml_source(toml_file)
    assert data["app"]["name"] == "Demo"
    assert prov["app.name"].name == "app.name"


def test_dotenv_source_provenance_uses_original_key(tmp_path, basic_schema):
    env_file = tmp_path / ".env"
    env_file.write_text("MYAPP_APP__NAME=demo\n", encoding="utf-8")
    _, prov = dotenv_source(env_file, prefix="MYAPP", schema=basic_schema)
    assert prov["app.name"].name == "MYAPP_APP__NAME"
